"""
View: Dedicated Hybrid Authentication & Man-in-the-Middle (MitM) Deep-Dive.
Displays a realistic step-by-step simulation where Eve runs two independent
BB84 key exchanges — one with Alice and one with Bob.
"""
import streamlit as st
from attacks.mitm import MitMAttack
from auth.wegman_carter import WegmanCarterAuth
from auth.classical_auth import ClassicalAuthenticator

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
        is_auth = ("Hybrid Authenticated" in auth_mode)

        with st.spinner("Running realistic MitM simulation — Eve performing two independent BB84 key exchanges..."):
            attack = MitMAttack(tamper_message=True, modified_text=eve_tamper)
            mitm_res = attack.execute_attack(
                num_qubits=32,
                original_plaintext=alice_msg,
                is_authenticated=is_auth,
                auth_key=preshared_key,
            )

        # ── Results ──────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📡 Attack Interception Architecture")

        # ── Phase 1: Quantum Key Exchange Visualization ──────────
        st.markdown("##### 🔬 Phase 1 — Quantum Channel Interception")
        st.caption(
            "Eve physically intercepts the quantum channel. She measures Alice's qubits "
            "(establishing K_AE), then re-prepares new qubits and sends them to Bob (establishing K_EB)."
        )

        leg1 = mitm_res.alice_eve_exchange
        leg2 = mitm_res.eve_bob_exchange

        # Show the two independent key exchanges side by side
        tab_leg1, tab_leg2 = st.tabs(["🔗 Leg 1: Alice → Eve", "🔗 Leg 2: Eve → Bob"])

        with tab_leg1:
            st.markdown("**Eve impersonates Bob** — measures Alice's qubits with her own random bases.")
            col_a, col_e1 = st.columns(2)
            with col_a:
                st.markdown("###### 👩‍🦰 Alice (Sender)")
                st.write(f"**Random Bits:** `{''.join(str(b) for b in leg1.sender_bits[:16])}...`")
                st.write(f"**Bases (0=Z, 1=X):** `{''.join(str(b) for b in leg1.sender_bases[:16])}...`")
            with col_e1:
                st.markdown("###### 👿 Eve (Receiver, pretending to be Bob)")
                st.write(f"**Eve's Bases:** `{''.join(str(b) for b in leg1.receiver_bases[:16])}...`")
                st.write(f"**Eve's Measured Bits:** `{''.join(str(b) for b in leg1.receiver_measured[:16])}...`")

            st.write(f"**Matching basis positions:** {leg1.matching_indices[:12]}{'...' if len(leg1.matching_indices) > 12 else ''}")
            st.write(f"**Sifted key K_AE ({len(leg1.sifted_sender)} bits):** `{''.join(str(b) for b in leg1.sifted_sender)}`")
            st.write(f"**QBER (Alice ↔ Eve):** {leg1.qber*100:.1f}%")

        with tab_leg2:
            st.markdown("**Eve impersonates Alice** — prepares new qubits from her measurements and sends to Bob.")
            col_e2, col_b = st.columns(2)
            with col_e2:
                st.markdown("###### 👿 Eve (Sender, pretending to be Alice)")
                st.write(f"**Eve's Re-Sent Bits:** `{''.join(str(b) for b in leg2.sender_bits[:16])}...`")
                st.write(f"**Eve's Bases:** `{''.join(str(b) for b in leg2.sender_bases[:16])}...`")
            with col_b:
                st.markdown("###### 🧔 Bob (Receiver)")
                st.write(f"**Bob's Bases:** `{''.join(str(b) for b in leg2.receiver_bases[:16])}...`")
                st.write(f"**Bob's Measured Bits:** `{''.join(str(b) for b in leg2.receiver_measured[:16])}...`")

            st.write(f"**Matching basis positions:** {leg2.matching_indices[:12]}{'...' if len(leg2.matching_indices) > 12 else ''}")
            st.write(f"**Sifted key K_EB ({len(leg2.sifted_sender)} bits):** `{''.join(str(b) for b in leg2.sifted_receiver)}`")
            st.write(f"**QBER (Eve ↔ Bob):** {leg2.qber*100:.1f}%")

        st.info(
            f"🔑 **Eve now holds both keys:**\n"
            f"- **K_AE** (shared with Alice): `{''.join(str(b) for b in mitm_res.alice_eve_key[:20])}{'...' if len(mitm_res.alice_eve_key) > 20 else ''}`\n"
            f"- **K_EB** (shared with Bob): `{''.join(str(b) for b in mitm_res.eve_bob_key[:20])}{'...' if len(mitm_res.eve_bob_key) > 20 else ''}`"
        )

        st.markdown("---")

        # ── Phase 2: Classical Channel & Authentication ──────────
        st.markdown("##### 📢 Phase 2 — Classical Channel (Basis Announcement & Authentication)")

        if is_auth:
            st.markdown(
                "Alice authenticates her basis announcement with a **Wegman-Carter tag** "
                "computed using the pre-shared key `K_auth`. Eve cannot forge this tag."
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("###### 👩‍🦰 Alice")
                basis_str = ",".join(str(b) for b in leg1.sender_bases)
                real_tag = WegmanCarterAuth.compute_tag(basis_str, preshared_key)
                st.write("**Announces bases + auth tag:**")
                st.code(f"Bases: {','.join(str(b) for b in leg1.sender_bases[:8])}...")
                st.code(f"Tag: {real_tag[:24]}...")

            with c2:
                st.markdown("###### 👿 Eve (Adversary)")
                st.error("🚨 **FORGERY ATTEMPT BLOCKED**")
                st.write("Eve intercepts Alice's announcement but needs to send **her own bases** to Bob.")
                st.write("Eve tries to forge a tag for her bases without `K_auth`:")
                eve_basis_str = ",".join(str(b) for b in leg1.receiver_bases)
                fake_tag = WegmanCarterAuth.compute_tag(eve_basis_str, "EVE_FAKE_KEY")
                st.code(f"Eve's Tag: {fake_tag[:24]}...")
                st.caption("Tag verification fails — mathematical congruency over Mersenne prime 2^127 − 1.")

            with c3:
                st.markdown("###### 🧔 Bob")
                st.success("🛡️ **INTEGRITY PRESERVED**")
                st.write("**Bob verifies the auth tag:**")
                st.error("Authentication Tag Mismatch! Connection terminated immediately. No message accepted.")
        else:
            st.markdown(
                "**No authentication** — Alice announces her bases in the clear. "
                "Eve intercepts and substitutes her own bases when forwarding to Bob."
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("###### 👩‍🦰 Alice")
                st.write("**Announces bases (no auth tag):**")
                st.code(f"Bases: {','.join(str(b) for b in leg1.sender_bases[:12])}...")
                st.caption("Sent in the clear — no authentication tag attached.")

            with c2:
                st.markdown("###### 👿 Eve (Adversary)")
                st.warning("⚠️ **INTERCEPTION SUCCESSFUL**")
                st.write("Eve sifts with Alice using Alice's real bases → gets **K_AE**.")
                st.write("Eve then sends **her own bases** to Bob (impersonating Alice) → establishes **K_EB**.")
                st.code(f"Eve→Bob bases: {','.join(str(b) for b in leg1.receiver_bases[:12])}...")

            with c3:
                st.markdown("###### 🧔 Bob")
                st.error("💀 **BOB DECEIVED**")
                st.write("Bob receives Eve's bases, thinks they're Alice's.")
                st.write("Bob sifts normally — establishes K_EB with Eve (believing it's Alice).")

        st.markdown("---")

        # ── Phase 3: Message Relay (only for unauthenticated) ────
        if not is_auth:
            st.markdown("##### 💬 Phase 3 — Message Encryption, Interception & Forgery")
            st.caption(
                "Alice encrypts her message with K_AE. Eve decrypts with K_AE, reads/modifies it, "
                "re-encrypts with K_EB, and forwards to Bob. Bob decrypts with K_EB."
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("###### 👩‍🦰 Alice")
                st.write(f"**Original Plaintext:**")
                st.code(alice_msg)
                st.write("**Encrypts with K_AE →**")
                ct_display = mitm_res.alice_ciphertext_hex
                st.code(ct_display[:48] + ("..." if len(ct_display) > 48 else ""))

            with c2:
                st.markdown("###### 👿 Eve (Adversary)")
                st.warning("⚠️ **FULL READ/WRITE ACCESS**")
                st.write("**Eve decrypts with K_AE →**")
                st.code(mitm_res.intercepted_message)
                st.write("**Eve forges new message:**")
                st.code(mitm_res.forged_message)
                st.write("**Re-encrypts with K_EB →**")
                if mitm_res.eve_ciphertext_hex:
                    eve_ct = mitm_res.eve_ciphertext_hex
                    st.code(eve_ct[:48] + ("..." if len(eve_ct) > 48 else ""))

            with c3:
                st.markdown("###### 🧔 Bob")
                st.error("💀 **BOB DECEIVED**")
                st.write("**Bob decrypts with K_EB →**")
                st.code(mitm_res.bob_received_message)
                st.caption("Bob believes this came authentically from Alice!")

        st.markdown("---")

        # ── Security Verdict ─────────────────────────────────────
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
