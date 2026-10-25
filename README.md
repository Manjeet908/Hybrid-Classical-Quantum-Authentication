# ⚛️ Hybrid Quantum Authentication & QKD Suite

A unified, interactive Quantum Key Distribution (QKD) and Hybrid Authentication simulator built with **Qiskit 2.5** and **Streamlit**. 

This suite provides end-to-end simulations of **BB84**, **B92**, and **E91** protocols, models realistic quantum attacks (**Intercept-Resend** and **Man-in-the-Middle**), and demonstrates why **Hybrid Classical-Quantum Authentication** (Wegman-Carter Universal Hashing) is essential to secure quantum communication networks.

---

## 🌟 Key Features

1. **Core QKD Protocols**:
   - **BB84 (Bennett & Brassard 1984)**: 4-state encoding across Rectilinear ($Z$) and Diagonal ($X$) bases with Shannon error correction bound ($11.0\%$ QBER limit).
   - **B92 (Bennett 1992)**: 2-state non-orthogonal encoding ($|0\rangle, |+\rangle$) with Unambiguous State Discrimination (USD) and conclusive detection filtering ($4.8\%$ QBER cutoff).
   - **E91 (Ekert 1991)**: Entanglement-based protocol using EPR Bell pairs ($|\Phi^+\rangle$) with automated Clauser-Horne-Shimony-Holt (CHSH) Bell inequality validation ($|S| > 2.0$ confirms maximal entanglement and absence of eavesdroppers).
   - **Adaptive Hybrid Mode**: Dynamic channel condition monitor that automatically recommends and routes between BB84, B92, and E91 based on real-time channel noise and hardware constraints.

2. **Adversarial Attack Simulation**:
   - **Intercept-Resend Attack**: Eve measures flying qubits in transit and resends collapsed states. Formulates the exact theoretical $25\%$ QBER spike in BB84.
   - **Man-in-the-Middle (MitM) Attack**: Eve intercepts both quantum signals and unauthenticated classical basis discussion. Demonstrates how unauthenticated channels are compromised with 0% QBER, and how Wegman-Carter authentication immediately detects and neutralizes the attack.
   - **Channel Noise**: Configurable fiber depolarizing and bit-flip channel noise models.

3. **Hybrid Authentication & Key Expansion**:
   - **Wegman-Carter Universal Hash Functions**: Information-theoretic classical authentication over Mersenne prime $p = 2^{127}-1$.
   - **Continuous Key Recycling**: Automatically recycles distilled quantum key bits into the classical authentication pool for continuous, self-renewing quantum secrecy.

4. **Modern High-Tech Streamlit Dashboard**:
   - Step-by-step transmission logs (Alice prep $\to$ Channel & Eve $\to$ Bob measurement $\to$ Sifting $\to$ Error Estimation $\to$ Key Distillation).
   - Dynamic Qiskit quantum circuit visualization (`qc.draw('mpl')`).
   - Quantum Cryptography Academy with complete theoretical proofs and formulas.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Qiskit, Qiskit-Aer, Streamlit, Matplotlib, Pylatexenc

### Installation
```bash
cd "quantum-auth-suite"
pip install -r requirements.txt
```

### Running the Application
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

## 📁 Repository Structure
```
quantum-auth-suite/
│
├── app.py                          # Main Streamlit Dashboard entry point
├── requirements.txt                # Dependency specifications
├── README.md                       # Comprehensive documentation
│
├── core/                           # Quantum Simulation Engine (Qiskit 2.5)
│   ├── qiskit_engine.py            # AerSimulator wrapper (Matrix Product State)
│   ├── bb84.py                     # BB84 protocol implementation
│   ├── b92.py                      # B92 protocol implementation
│   ├── e91.py                      # E91 entanglement & Bell protocol
│   └── hybrid_engine.py            # Adaptive protocol selector & hybrid engine
│
├── attacks/                        # Eavesdropping & Channel Degradation Models
│   ├── intercept_resend.py         # Eve intercept-measure-resend
│   ├── mitm.py                     # Classical & Quantum Man-in-the-Middle
│   └── noise_channel.py            # Depolarizing & phase/bit flip channel noise
│
├── auth/                           # Hybrid Authentication & Cryptography
│   ├── wegman_carter.py            # Wegman-Carter Universal Hash Message Authentication
│   └── classical_auth.py           # Classical authenticator & HMAC-SHA256
│
├── postprocessing/                 # Key Distillation & Security Verification
│   ├── sifting.py                  # Basis reconciliation & inconclusive filters
│   ├── chsh_evaluator.py           # CHSH S-parameter calculation (Cirel'son bound)
│   └── privacy_amp.py              # Parity reconciliation & Shannon privacy amplification
│
└── ui/                             # Streamlit UI & Visualizations
    ├── styles.py                   # Cyberpunk dark theme CSS & tokens
    ├── circuit_renderer.py         # Dynamic Qiskit MPL circuit diagram generator
    ├── views_simulator.py          # Interactive single protocol lab
    ├── views_hybrid_auth.py        # MitM vs Hybrid Authentication playground
    └── views_theory.py             # Theory academy & mathematical proofs
```
