"""
View: Interactive Single Protocol Simulator for BB84, B92, E91, and Adaptive Hybrid.
"""
import streamlit as st
import pandas as pd
import numpy as np

from core.bb84 import BB84Protocol
from core.b92 import B92Protocol
from core.e91 import E91Protocol
from core.hybrid_engine import HybridAuthEngine
from attacks.intercept_resend import InterceptResendAttack
from ui.circuit_renderer import draw_quantum_circuit
from ui.styles import render_badge

def render_simulator_view():
    st.markdown("### 🔬 Interactive Quantum Key Distribution Laboratory")
    st.markdown(
        "Configure quantum parameters, simulate channel conditions and adversarial attacks, "
        "and observe step-by-step state collapse, sifting reconciliation, and key distillation."
    )

    # Top Control Bar
    col_proto, col_attack, col_qubits = st.columns([1.2, 1.2, 1.0])
    
    with col_proto:
        protocol_choice = st.selectbox(
            "Protocol Architecture",
            ["BB84 (4-State)", "B92 (2-State Non-Orthogonal)", "E91 (EPR Bell Entanglement)"]
        )
        # ["BB84 (4-State)", "B92 (2-State Non-Orthogonal)", "E91 (EPR Bell Entanglement)", "Adaptive Hybrid"]

    with col_attack:
        attack_choice = st.selectbox(
            "Channel Eavesdropping / Threat Model",
            ["None (Ideal Secure Channel)", "Intercept-Resend Attack"]
        )

    with col_qubits:
        qubit_count = st.slider("Qubit / Pair Count", min_value=12, max_value=48, value=24, step=4)

    # Attack & Noise Sliders
    col_noise, col_param = st.columns(2)
    with col_noise:
        noise_level = st.slider(
            "Channel Depolarizing Noise (ε)",
            min_value=0.0, max_value=0.30, value=0.0, step=0.02,
            help="Simulates environmental fiber decoherence and detector dark counts."
        )

    with col_param:
        if attack_choice == "Intercept-Resend Attack":
            eve_intensity = st.slider(
                "Eve Interception Rate",
                min_value=0.1, max_value=1.0, value=1.0, step=0.1,
                help="Fraction of flying qubits intercepted and measured by Eve."
            )
        else:
            st.info("💡 Secure channel configured. No adversary injected.")

    # Execution Trigger
    run_btn = st.button("🚀 Execute Quantum Simulation", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Preparing states and executing quantum circuit on AerSimulator..."):
            attack_obj = None
            if attack_choice == "Intercept-Resend Attack":
                attack_obj = InterceptResendAttack(intercept_prob=eve_intensity)

            # Route to selected protocol
            if "BB84" in protocol_choice:
                runner = BB84Protocol()
                res = runner.run(num_qubits=qubit_count, attack=attack_obj, noise_level=noise_level)
                render_bb84_results(res)
            elif "B92" in protocol_choice:
                runner = B92Protocol()
                res = runner.run(num_qubits=qubit_count, attack=attack_obj, noise_level=noise_level)
                render_b92_results(res)
            elif "E91" in protocol_choice:
                runner = E91Protocol()
                res = runner.run(num_pairs=qubit_count, attack=attack_obj, noise_level=noise_level)
                render_e91_results(res)
            else:
                hybrid_engine = HybridAuthEngine()
                atk_type = "Intercept-Resend" if attack_choice == "Intercept-Resend Attack" else None
                atk_p = eve_intensity if attack_choice == "Intercept-Resend Attack" else 0.0
                res = hybrid_engine.run_hybrid_session(
                    num_qubits=qubit_count,
                    noise_level=noise_level,
                    attack_type=atk_type,
                    attack_param=atk_p
                )
                render_hybrid_results(res)


def render_bb84_results(res):
    """Renders BB84 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 BB84 Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    # Metric Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Qubits Sent", res.num_qubits)
    m2.metric("Sifted Key Length", f"{res.sifting_result.sifted_key_length} bits", f"{res.sifting_result.sifting_ratio*100:.1f}% yield")
    m3.metric("Error Count", f"{res.sifting_result.error_count} bits")
    
    delta_color = "normal" if res.sifting_result.qber <= 0.11 else "inverse"
    m4.metric("QBER", f"{res.sifting_result.qber*100:.1f}%", f"Limit: {res.sifting_result.security_threshold*100:.1f}%", delta_color=delta_color)
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits", f"{res.distillation_result.compression_ratio*100:.0f}% distilled")

    # Security Alert Box
    if res.security_status == "COMPROMISED":
        st.error(
            f"🚨 **SESSION ABORTED:** QBER ({res.sifting_result.qber*100:.1f}%) exceeds the 11.0% Shannon security limit! "
            f"Adversary detection triggered. Sifted bits discarded to prevent key leakage."
        )
    elif res.security_status == "WARNING":
        st.warning("⚠️ **ELEVATED NOISE:** QBER is elevated. Privacy amplification required higher compression.")
    else:
        st.success(f"🎉 **SECURE SECRET KEY ESTABLISHED:** Distilled key hex: `{res.distillation_result.final_hex_key}`")

    # Detailed Step-by-Step Transmission Table
    with st.expander("🔍 Step-by-Step Bit & Measurement Transmission Log", expanded=True):
        basis_names = {0: "Z (|0⟩,|1⟩)", 1: "X (|+⟩,|-⟩)"}
        eve_bases = res.intercept_result.eve_bases if res.intercept_result else [None]*res.num_qubits
        eve_bits = res.intercept_result.eve_bits if res.intercept_result else [None]*res.num_qubits

        df_data = []
        for i in range(res.num_qubits):
            matched = (i in res.sifting_result.matching_indices)
            is_err = matched and (res.alice_bits[i] != res.bob_measured_bits[i])
            df_data.append({
                "Alice Bit": res.alice_bits[i],
                "Alice Basis": basis_names[res.alice_bases[i]],
                "Eve Intercepted?": "👿 YES" if (res.intercept_result and res.intercept_result.intercepted[i]) else "—",
                "Eve Basis": basis_names.get(eve_bases[i], "—") if (res.intercept_result and res.intercept_result.intercepted[i]) else "—",
                "Bob Basis": basis_names[res.bob_bases[i]],
                "Bob Measured": res.bob_measured_bits[i],
                "Bases Match?": "✅ Sifted" if matched else "❌ Discard",
                "Error Status": "🚨 ERROR" if is_err else ("✅ OK" if matched else "—")
            })
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=280)

    # Circuit Diagram
    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        st.caption("Displays the quantum register, Alice's preparation, channel barriers, and Bob's measurements.")
        fig = draw_quantum_circuit(res.circuit, max_qubits_to_draw=res.num_qubits)
        st.pyplot(fig)


def render_b92_results(res):
    """Renders B92 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 B92 Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Qubits Sent", res.num_qubits)
    m2.metric("Conclusive Detections", f"{res.sifting_result.sifted_key_length} bits", f"{res.sifting_result.sifting_ratio*100:.1f}% yield")
    m3.metric("Inconclusive Discards", f"{res.num_qubits - res.sifting_result.sifted_key_length} bits")
    
    delta_color = "normal" if res.sifting_result.qber <= 0.048 else "inverse"
    m4.metric("QBER", f"{res.sifting_result.qber*100:.1f}%", f"Limit: 4.8%", delta_color=delta_color)
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits")

    if res.security_status == "COMPROMISED":
        st.error(
            f"🚨 **SESSION ABORTED:** B92 QBER ({res.sifting_result.qber*100:.1f}%) exceeds the 4.8% cutoff! "
            f"B92 is highly sensitive to noise and eavesdropping."
        )
    else:
        st.success(f"🎉 **SECURE B92 KEY ESTABLISHED:** Distilled key hex: `{res.distillation_result.final_hex_key}`")

    with st.expander("🔍 B92 Conclusive vs Inconclusive Measurement Log", expanded=True):
        b92_basis_desc = {0: "Basis 0 (Test |1⟩)", 1: "Basis 1 (Test |−⟩)"}
        df_data = []
        for i in range(res.num_qubits):
            is_conc = res.bob_conclusive[i]
            inferred = res.bob_inferred_bits[i]
            is_err = is_conc and (res.alice_bits[i] != inferred)
            df_data.append({
                "Qubit #": i,
                "Alice Bit": res.alice_bits[i],
                "Alice State": res.alice_states[i],
                "Bob Test Operator": b92_basis_desc[res.bob_bases[i]],
                "Bob Measurement": res.bob_raw_measurements[i],
                "Detection Result": "✅ CONCLUSIVE" if is_conc else "⚪ Inconclusive",
                "Bob Inferred Bit": inferred if is_conc else "—",
                "Match Status": "🚨 ERROR" if is_err else ("✅ Match" if is_conc else "—")
            })
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, height=280)

    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        fig = draw_quantum_circuit(res.circuit, res.num_qubits)
        st.pyplot(fig)


def render_e91_results(res):
    """Renders E91 execution cards and data tables."""
    st.markdown("---")
    st.markdown(f"#### 📊 E91 Entanglement Execution Overview {render_badge(res.security_status)}", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("EPR Pairs Generated", res.num_pairs)
    m2.metric("Key Generation Pairs", f"{res.sifting_result.sifted_key_length} pairs")
    
    chsh_color = "normal" if res.chsh_result.is_violated else "inverse"
    m3.metric("CHSH Bell Parameter |S|", f"{res.chsh_result.s_value:.3f}", "Bound: > 2.0", delta_color=chsh_color)
    m4.metric("QBER on Key Pairs", f"{res.sifting_result.qber*100:.1f}%")
    m5.metric("Final Secret Key", f"{len(res.distillation_result.final_secret_key)} bits")

    st.info(res.chsh_result.security_verdict)

    with st.expander("🔍 CHSH Correlation Terms & Key Basis Alignment", expanded=True):
        col_chsh, col_table = st.columns([1, 1.4])
        with col_chsh:
            st.markdown("**CHSH 4-Correlation Components:**")
            for term, val in res.chsh_result.correlation_terms.items():
                st.write(f"- `{term}`: **{val:+.3f}**")
            st.markdown(f"**Calculated |S|:** `{res.chsh_result.s_value:.4f}`")
            st.caption("Classical limit ≤ 2.0. Quantum maximum (Cirel'son bound) = 2.8284.")
        
        with col_table:
            st.markdown("**Aligned Key Generation Samples:**")
            df_e91 = pd.DataFrame({
                "Pair #": res.sifting_result.matching_indices,
                "Alice Measured": res.sifting_result.alice_sifted,
                "Bob Measured": res.sifting_result.bob_sifted,
                "Match?": ["✅" if a == b else "❌" for a, b in zip(res.sifting_result.alice_sifted, res.sifting_result.bob_sifted)]
            })
            st.dataframe(df_e91, use_container_width=True, height=200)

    with st.expander("⚡ Quantum Circuit Visualization (Qiskit MPL)", expanded=False):
        fig = draw_quantum_circuit(res.circuit, res.num_pairs)
        st.pyplot(fig)


def render_hybrid_results(res):
    """Renders Adaptive Hybrid results."""
    st.markdown("---")
    st.markdown(f"#### 🌐 Adaptive Hybrid Session Overview {render_badge(res.overall_security)}", unsafe_allow_html=True)
    
    st.info(f"**Adaptive Intelligence Verdict:** {res.adaptation_reason}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Protocol", res.selected_protocol)
    c2.metric("Classical Authentication", res.auth_scheme)
    c3.metric("Key Recycling Status", "ACTIVE")

    st.markdown("**MitM Security Check on Public Discussion:**")
    st.success(res.mitm_test_result.status_summary)
