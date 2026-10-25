"""
View: Quantum Cryptography Theory, Mathematical Foundations, and Security Proofs.
"""
import streamlit as st

def render_theory_view():
    st.markdown("### 📚 Quantum Cryptography & Authentication Academy")
    st.markdown(
        "A comprehensive theoretical guide to quantum key distribution, mathematical proofs, "
        "eavesdropping detection mechanics, and hybrid classical-quantum authentication."
    )

    tab_bb84, tab_b92, tab_e91, tab_attacks, tab_auth = st.tabs([
        "1. BB84 Protocol",
        "2. B92 Protocol",
        "3. E91 Protocol & CHSH",
        "4. Quantum Attacks",
        "5. Hybrid Authentication"
    ])

    with tab_bb84:
        st.markdown("#### BB84 (Bennett & Brassard, 1984)")
        st.markdown(r"""
        **Core Principle:** Employs the **No-Cloning Theorem** and the Heisenberg Uncertainty Principle to securely distribute keys.

        - **Quantum Encodings:**
          - **Rectilinear Basis ($Z$):** Bit $0 \to |0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$, Bit $1 \to |1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$
          - **Diagonal Basis ($X$):** Bit $0 \to |+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$, Bit $1 \to |-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$

        - **Basis Reconciliation (Sifting):**
          - Alice and Bob choose independent random bases for each qubit ($\Pr(\text{match}) = 0.5$).
          - On matching bases, in the absence of noise or eavesdropping, Bob's measurement is deterministic and identical to Alice's bit ($\Pr(\text{error}) = 0$).

        - **Shannon Security Threshold (11.0% QBER):**
          - The secret key fraction after error correction and privacy amplification is given by the Devetak-Winter bound:
            $$r = 1 - 2h(QBER)$$
            where $h(p) = -p \log_2(p) - (1-p) \log_2(1-p)$ is the binary Shannon entropy.
          - Solving $1 - 2h(p) = 0$ yields $p \approx 0.110027$ (**11.0%**).
          - If $QBER > 11\%$, Eve potentially holds more mutual information than Alice and Bob share, requiring session abortion!
        """)

    with tab_b92:
        st.markdown("#### B92 (Charles H. Bennett, 1992)")
        st.markdown(r"""
        **Core Principle:** Proved that **any two non-orthogonal quantum states** are sufficient to implement secure quantum key distribution, without needing four states!

        - **Alice's Encoding:**
          - Bit $0 \to |0\rangle$ (Rectilinear state)
          - Bit $1 \to |+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$ (Diagonal state)
          - Note the state overlap: $|\langle 0 | + \rangle|^2 = \frac{1}{2} \neq 0$ (Non-orthogonal).

        - **Bob's Unambiguous State Discrimination (USD):**
          - Bob cannot distinguish $|0\rangle$ and $|+\rangle$ with 100% certainty (forbidden by quantum mechanics).
          - Instead, Bob measures using projection operators orthogonal to the states:
            - **Basis 0:** Projects orthogonal to $|0\rangle$ (standard computational basis measurement). If Bob measures $1$, Alice could *not* have sent $|0\rangle$, so she definitely sent $|+\rangle$ (**Bit 1**).
            - **Basis 1:** Projects orthogonal to $|+\rangle$ (Hadamard measurement). If Bob measures $1$ (state $|-\rangle$), Alice could *not* have sent $|+\rangle$, so she definitely sent $|0\rangle$ (**Bit 0**).
            - If Bob measures $0$, the measurement is **inconclusive** and discarded.

        - **Efficiency & Noise Sensitivity:**
          - Conclusive detection probability: $\Pr(\text{conclusive}) = \frac{1}{4} = 25\%$.
          - Because conclusive detections are rare, channel noise has a magnified effect, leading to a much tighter security threshold (**~4.8% QBER**).
        """)

    with tab_e91:
        st.markdown("#### E91 Protocol (Artur Ekert, 1991) & Bell's Theorem")
        st.markdown(r"""
        **Core Principle:** Utilizes **quantum entanglement** (EPR pairs) and the violation of the **Clauser-Horne-Shimony-Holt (CHSH)** Bell inequality to provide **device-independent security**.

        - **Bell State Preparation:**
          An entangled pair source generates Bell states:
          $$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$$
          Qubit $A$ is sent to Alice; Qubit $B$ is sent to Bob.

        - **Measurement Bases & Angles:**
          - Alice chooses from angles $\theta_A \in \{a_1 = 0, a_2 = \frac{\pi}{4}, a_3 = \frac{\pi}{2}\}$.
          - Bob chooses from angles $\theta_B \in \{b_1 = \frac{\pi}{8}, b_2 = \frac{\pi}{4}, b_3 = \frac{3\pi}{8}\}$.

        - **Key Generation vs. Bell Test Partitioning:**
          - **Key Bits:** Formed by pairs where orientations match ($a_2 = b_2 = \frac{\pi}{4}$). Because $|\Phi^+\rangle$ has identical correlations at matched angles, Alice and Bob obtain identical bits!
          - **CHSH Eavesdropping Test:** Formed by the non-matching angle combinations $(a_1, b_1), (a_1, b_3), (a_3, b_1), (a_3, b_3)$.

        - **CHSH Inequality & Cirel'son's Bound:**
          $$S = |E(a_1, b_1) - E(a_1, b_3) - E(a_3, b_1) + E(a_3, b_3)|$$
          - **Classical Limit (Local Realism / Eavesdropped):** $|S| \le 2.0$
          - **Quantum Limit (Cirel'son's Bound):** $|S| = 2\sqrt{2} \approx 2.8284$
          - **Security Proof:** If $|S| > 2.0$, quantum non-locality proves that no local hidden variable or eavesdropper has disturbed the entangled channel!
        """)

    with tab_attacks:
        st.markdown("#### Quantum Attack Vectors")
        st.markdown(r"""
        ##### 1. Intercept-Resend Attack
        - Eve intercepts the flying qubit in the optical channel, measures it in random basis (Z or X), and prepares a replacement state to forward to Bob.
        - In BB84:
          - If Alice and Bob choose matching bases (50% probability):
            - If Eve guessed the same basis (50%): Bob gets Alice's bit (0% error).
            - If Eve guessed the opposite basis (50%): Bob gets random bit (50% error).
          - Total expected QBER on the sifted key:
            $$QBER = 0.5 \times 0 + 0.5 \times 0.5 = 0.25 = \mathbf{25\%}$$
          - Since $25\% > 11\%$, Eve is immediately detected!

        ##### 2. Man-in-the-Middle (MitM) Attack
        - QKD only detects eavesdropping on the *quantum* channel. If the *classical* channel (used for basis announcement and error estimation) is unauthenticated:
          - Eve impersonates Bob to Alice and Alice to Bob.
          - Eve establishes two independent keys: $K_{AE}$ and $K_{EB}$.
          - Neither party detects any QBER! Eve transparently decrypts and re-encrypts all traffic.
          - **Mitigation:** Requires **Hybrid Quantum-Classical Authentication**.
        """)

    with tab_auth:
        st.markdown("#### Hybrid Classical-Quantum Authentication & Key Recycling")
        st.markdown(r"""
        ##### Why QKD Needs Classical Authentication
        To prevent MitM attacks, every classical message exchanged over the public channel must be authenticated with **unconditional information-theoretic security** (matching the security level of QKD itself).

        ##### Wegman-Carter Universal Hashing
        - Invented by Mark Wegman and J. Lawrence Carter (1981).
        - Uses a Strongly Universal Hash Family ($U_2$) defined over a large Mersenne prime $p = 2^{127} - 1$:
          $$Tag = (a \cdot m + b) \pmod p$$
          where $m$ is the hash of the classical basis message, and $(a, b)$ are derived from a pre-shared secret key $K_{\text{auth}}$.
        - **Security Property:** Even an adversary with infinite quantum computational power cannot forge an authentic tag with probability greater than $\frac{1}{p} \approx 10^{-38}$.

        ##### Continuous Quantum Key Recycling Loop (Key Expansion)
        ```
        [Pre-Shared Seed (128 bits)]
                   │
                   ▼
        [Authenticate Public Basis Exchange (64 bits)]
                   │
                   ▼
        [QKD Distillation Pipeline (BB84 / B92 / E91)]
                   │
                   ▼
        [Generate 2,048 Secure Quantum Key Bits]
                   │
          ┌────────┴──────────────────────────┐
          ▼                                   ▼
        [Recycle 128 bits into Auth Pool]   [Use 1,920 bits for AES/OTP]
          │
          └────────► Next QKD Session (Infinite Secure Loop!)
        ```
        This transforms QKD from a simple key distributor into a self-sustaining **Quantum Key Expansion System**.
        """)
