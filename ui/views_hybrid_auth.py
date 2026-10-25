"""
View: Dedicated Hybrid Authentication & Man-in-the-Middle (MitM) Deep-Dive.
"""
import streamlit as st
from attacks.mitm import MitMAttack
from auth.wegman_carter import WegmanCarterAuth
from auth.classical_auth import ClassicalAuthenticator
from core.bb84 import BB84Protocol

def render_hybrid_auth_view():
    st.markdown("### 🛡️ Hybrid Quantum Authentication & MitM Attack Defense")
    st.markdown(
        "A fundamental principle in Quantum Cryptography is that **QKD provides unconditional confidentiality, "
        "but relies on an authenticated classical channel to prevent Man-in-the-Middle (MitM) attacks**. "
        "Explore how classical Wegman-Carter Universal Hashing creates an impenetrable hybrid defense."
    )

    # Configuration Controls
    col_mode, col_scheme = st.columns(2)
    with col_mode:
        auth_mode = st.radio(
            "Classical Channel Security Configuration",
            ["Unauthenticated Channel (Vulnerable to MitM)", "Hybrid Authenticated Channel (Wegman-Carter / HMAC)"],
            index=1
        )
    with col_scheme:
        scheme_choice = st.selectbox(
            "Authentication Algorithm",
            ["Wegman-Carter (Information-Theoretic)", "HMAC-SHA256 (Post-Quantum Symmetric)"]
        )

    # Simulation Parameters
    col_msg, col_tamper = st.columns([1.5, 1])
    with col_msg:
        alice_msg = st.text_input("Alice's Secret Transaction Message", value="AUTHORIZE TRANSFER: $500,000 TO ACCT #8841")
    with col_tamper:
        eve_tamper = st.text_input("Eve's Forged Malicious Message", value="AUTHORIZE TRANSFER: $500,000 TO EVE #6660")

    preshared_key = st.text_input("Pre-Shared Classical Secret Key (K_auth)", value="QC_PRESHARED_AUTH_SEED_2026", type="password")

    run_sim = st.button("⚡ Test Channel Interception & Authentication", type="primary", use_container_width=True)

    if run_sim:
        with st.spinner("Simulating classical channel interception..."):
            # Run BB84 to generate initial keys
            bb84 = BB84Protocol()
            res = bb84.run(num_qubits=32, attack=None, noise_level=0.0)
            alice_key = res.sifting_result.alice_sifted
            bob_key = res.sifting_result.bob_sifted

            is_auth = ("Hybrid Authenticated" in auth_mode)
            attack = MitMAttack(tamper_message=True, modified_text=eve_tamper)
            mitm_res = attack.execute_attack(
                alice_key=alice_key,
                bob_key=bob_key,
                original_plaintext=alice_msg,
                is_authenticated=is_auth,
                auth_key=preshared_key
            )

            st.markdown("---")
            st.markdown("#### 📡 Attack Interception Architecture")

            # Diagram / Workflow Representation
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("##### 👩‍🦰 Alice")
                st.write(f"**Original Plaintext:**")
                st.code(alice_msg)
                if is_auth:
                    tag = WegmanCarterAuth.compute_tag(alice_msg, preshared_key)
                    st.write(f"**Classical Auth Tag (Wegman-Carter):**")
                    st.code(tag[:16] + "...")
                else:
                    st.caption("Classical messages transmitted in the clear (no authentication tag).")

            with c2:
                st.markdown("##### 👿 Eve (Adversary)")
                if is_auth:
                    st.error("🚨 **FORGERY ATTEMPT BLOCKED**")
                    st.write("Eve attempts to replace Alice's message, but does not possess `K_auth`.")
                    fake_tag = WegmanCarterAuth.compute_tag(eve_tamper, "EVE_FAKE_KEY")
                    st.write(f"**Eve's Invalid Tag:**")
                    st.code(fake_tag[:16] + "...")
                    st.caption("Tag verification fails mathematical congruency over Mersenne prime 2^127 - 1.")
                else:
                    st.warning("⚠️ **INTERCEPTION SUCCESSFUL**")
                    st.write("**Eve Decrypted Plaintext:**")
                    st.code(mitm_res.intercepted_message)
                    st.write("**Eve Injected Forgery:**")
                    st.code(mitm_res.forged_message)

            with c3:
                st.markdown("##### 🧔 Bob")
                if is_auth:
                    st.success("🛡️ **INTEGRITY PRESERVED**")
                    st.write("**Bob's Action:**")
                    st.error("Authentication Tag Mismatch! Connection terminated immediately. No message accepted.")
                else:
                    st.error("💀 **BOB DECEIVED**")
                    st.write("**Bob Received & Decrypted:**")
                    st.code(mitm_res.bob_received_message)
                    st.caption("Bob believes this came authentically from Alice!")

            st.markdown("---")
            if is_auth:
                st.success(
                    "✅ **SECURITY VERDICT: ATTACK NEUTRALIZED.** "
                    "By combining QKD with classical Wegman-Carter polynomial evaluation, the hybrid protocol achieves "
                    "**unconditional information-theoretic authentication**. Eve cannot alter basis announcements or inject ciphertext."
                )
            else:
                st.error(
                    "❌ **SECURITY VERDICT: COMPLETE SYSTEM COMPROMISE.** "
                    "Without classical channel authentication, QKD is vulnerable to Man-in-the-Middle impersonation. "
                    "Even with 0% QBER on the quantum link, the classical channel must be authenticated!"
                )

            # Key Recycling explanation
            with st.expander("🔄 Continuous Quantum Key Recycling Explained", expanded=False):
                st.markdown("""
                **How QKD replenishes authentication keys:**
                1. Alice & Bob start with a small pre-shared classical seed key (e.g. 128 bits).
                2. They use a small fraction (e.g. 64 bits) to authenticate the QKD public sifting channel.
                3. The quantum key distribution generates thousands of new unconditionally secure key bits.
                4. A portion of the newly generated quantum key is **recycled** to become the authentication key for the *next* QKD session.
                5. This achieves an infinite, self-renewing, unconditionally secure cryptographic loop (**Key Expansion**)!
                """)
