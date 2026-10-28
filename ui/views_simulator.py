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

    with col_attack:
        attack_choice = st.selectbox(
            "Channel Eavesdropping / Threat Model",
            [
                "None (Ideal Secure Channel)",
                "Intercept-Resend Attack (Quantum Channel)",
                "Man-in-the-Middle Attack (Channel & Classical Relay)"
            ]
        )

    with col_qubits:
        qubit_count = st.slider(
            "Qubit / Pair Count",
            min_value=12, max_value=120, value=24, step=4,
            help="Higher count (e.g. 60-100) provides tighter statistical convergence for CHSH Bell tests."
        )

    # Attack & Noise Configuration
    col_noise, col_param = st.columns(2)
    with col_noise:
        noise_level = st.slider(
            "Channel Depolarizing Noise (ε)",
            min_value=0.0, max_value=0.30, value=0.0, step=0.02,
            help="Simulates environmental fiber decoherence and detector dark counts."
        )

    with col_param:
        if "Intercept-Resend" in attack_choice:
            eve_intensity = st.slider(
                "Eve Interception Rate",
                min_value=0.1, max_value=1.0, value=1.0, step=0.1,
                help="Fraction of flying qubits intercepted and measured by Eve in transit."
            )
        elif "Man-in-the-Middle" in attack_choice:
            auth_mode = st.radio(
                "Classical Channel Authentication",
                ["Unauthenticated Channel (Vulnerable to MitM)", "Hybrid Authenticated Channel (Wegman-Carter)"],
                index=0,
                help="Wegman-Carter universal hashing prevents Eve from impersonating Alice or Bob during basis reconciliation."
            )
        else:
            st.info("💡 Secure channel configured. No adversary injected.")

    # Execution Trigger
    run_btn = st.button("🚀 Execute Quantum Simulation", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Preparing states and executing quantum circuit on AerSimulator..."):
            # Handle Man-in-the-Middle Attack route
            if "Man-in-the-Middle" in attack_choice:
                from attacks.mitm import MitMAttack
                is_auth = ("Hybrid Authenticated" in auth_mode)
                mitm_runner = MitMAttack(tamper_message=True, modified_text="MALICIOUS TAMPERED TRANSACTION: $1,000,000 TO EVE")
                mitm_res = mitm_runner.execute_attack(
                    num_qubits=qubit_count,
                    original_plaintext="AUTHORIZE TRANSFER: $500,000 TO ACCT #8841",
                    is_authenticated=is_auth,
                    auth_key="PRESHARED_SECRET_SEED_2026"
                )
                render_mitm_inline_results(mitm_res)
                return

            attack_obj = None
            if "Intercept-Resend" in attack_choice:
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
        eve_bases = res.intercept_result.eve_bases if res.intercept_result else [None]*res.num_qubits
        eve_bits = res.intercept_result.eve_bits if res.intercept_result else [None]*res.num_qubits

        df_data = []
        for i in range(res.num_qubits):
            is_conc = res.bob_conclusive[i]
            inferred = res.bob_inferred_bits[i]
            is_err = is_conc and (res.alice_bits[i] != inferred)
            row = {
                "Qubit #": i,
                "Alice Bit": res.alice_bits[i],
                "Alice State": res.alice_states[i],
            }
            if res.intercept_result:
                was_int = res.intercept_result.intercepted[i]
                row["Eve Intercepted?"] = "👿 YES" if was_int else "—"
                row["Eve Basis"] = ("Z" if eve_bases[i] == 0 else "X") if was_int else "—"
                row["Eve Measured"] = eve_bits[i] if (was_int and eve_bits[i] is not None) else "—"
            row.update({
                "Bob Test Operator": b92_basis_desc[res.bob_bases[i]],
                "Bob Measurement": res.bob_raw_measurements[i],
                "Detection Result": "✅ CONCLUSIVE" if is_conc else "⚪ Inconclusive",
                "Bob Inferred Bit": inferred if is_conc else "—",
                "Match Status": "🚨 ERROR" if is_err else ("✅ Match" if is_conc else "—")
            })
            df_data.append(row)
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

    if res.intercept_result:
        st.warning(
            f"👿 **Adversary Interception:** Eve intercepted {res.intercept_result.qubits_intercepted_count} of {res.num_pairs} transiting photons ({res.intercept_result.interception_rate*100:.1f}%), "
            f"collapsing entanglement and breaking Bell inequality violation!"
        )

    if res.num_pairs < 48:
        st.caption("💡 *Tip: CHSH Bell evaluation tests 4 correlation terms over 9 random basis combinations. For high statistical certainty (|S| > 2.0 with minimal variance), increase pair count to ≥ 60–100.*")

    with st.expander("🔍 CHSH Correlation Terms & Key Basis Alignment", expanded=True):
        col_chsh, col_table = st.columns([1, 1.4])
        with col_chsh:
            st.markdown("**CHSH 4-Correlation Components:**")
            for term, val in res.chsh_result.correlation_terms.items():
                st.write(f"- `{term}`: **{val:+.3f}** (samples: {res.chsh_result.sample_counts.get(term, 0)})")
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


def render_mitm_inline_results(mitm_res):
    """Renders Man-in-the-Middle attack execution within the simulator."""
    st.markdown("---")
    st.markdown("#### 🚨 Man-in-the-Middle (MitM) Attack Simulation Results")

    if mitm_res.is_authenticated and mitm_res.attack_detected:
        st.success(mitm_res.status_summary)
    else:
        st.error(mitm_res.status_summary)

    # Key Exchange Comparison between the two legs
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 🔗 Leg 1: Alice ↔ Eve (Eve poses as Bob)")
        leg1 = mitm_res.alice_eve_exchange
        st.write(f"**Sifted Key K_AE ({len(leg1.sifted_sender)} bits):** `{''.join(str(b) for b in leg1.sifted_sender)}`")
        st.write(f"**Leg 1 QBER:** {leg1.qber*100:.1f}% (No error between Alice and Eve!)")
    with col2:
        st.markdown("##### 🔗 Leg 2: Eve ↔ Bob (Eve poses as Alice)")
        leg2 = mitm_res.eve_bob_exchange
        st.write(f"**Sifted Key K_EB ({len(leg2.sifted_receiver)} bits):** `{''.join(str(b) for b in leg2.sifted_receiver)}`")
        st.write(f"**Leg 2 QBER:** {leg2.qber*100:.1f}% (No error between Eve and Bob!)")

    # Message Relay & Tampering Visualization
    st.markdown("##### ✉️ Message Interception & Decryption Relay")
    col_a, col_e, col_b = st.columns(3)
    with col_a:
        st.markdown("###### 👩‍🦰 Alice Transmits")
        st.text_area("Original Plaintext", value=mitm_res.original_plaintext, disabled=True, height=90)
    with col_e:
        st.markdown("###### 👿 Eve Intercepts & Modifies")
        eve_msg = mitm_res.forged_message if mitm_res.forged_message else "(Blocked before transmission)"
        st.text_area("Eve's Forged Message", value=eve_msg, disabled=True, height=90)
    with col_b:
        st.markdown("###### 🧔 Bob Receives")
        bob_msg = mitm_res.bob_received_message if mitm_res.bob_received_message else "(Connection Terminated - Tampering Blocked!)"
        st.text_area("Bob's Decrypted Message", value=bob_msg, disabled=True, height=90)

    # Classical Channel Authentication
    st.markdown("##### 🛡️ Classical Authentication Status")
    c_tag1, c_tag2 = st.columns(2)
    with c_tag1:
        st.write(f"**Alice's Basis Auth Tag:** `{mitm_res.alice_auth_tag}`")
    with c_tag2:
        st.write(f"**Eve's Forged Tag Attempt:** `{mitm_res.eve_auth_tag_attempt}`")

