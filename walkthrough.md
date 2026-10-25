# Walkthrough: Hybrid Quantum Authentication & QKD Suite

We have implemented a unified, interactive **Streamlit application** powered by **Qiskit 2.5**. The system simulates and compares three core quantum key distribution protocols (**BB84**, **B92**, and **E91**), models realistic quantum attacks (**Intercept-Resend** and **Man-in-the-Middle**), and demonstrates **Hybrid Classical-Quantum Authentication** using Wegman-Carter universal hashing.



## 🛠️ Architecture & Changes Made

### 1. Quantum Backend Engine ([`quantum-auth-suite/core/`])
- **`qiskit_engine.py`**: Configured `AerSimulator` with `method="matrix_product_state"`, enabling linear-scaling simulation for 100+ qubits without memory bottleneck. Added multi-register measurement extraction.
- **`bb84.py`**: Standard 4-state rectilinear ($Z$) and diagonal ($X$) encoding with basis reconciliation, sampling error estimation, and 11.0% Shannon security threshold.
- **`b92.py`**: 2-state non-orthogonal encoding ($|0\rangle, |+\rangle$) with Unambiguous State Discrimination (USD), conclusive detection filtering, and 4.8% noise cutoff.
- **`e91.py`**: Entanglement-based protocol using EPR Bell pairs ($|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$) and automated Clauser-Horne-Shimony-Holt (CHSH) Bell inequality evaluation.
- **`hybrid_engine.py`**: Dynamic condition monitor recommending BB84, B92, or E91 based on real-time channel noise and hardware constraints.

### 2. Quantum Attack Simulation Layer ([`quantum-auth-suite/attacks/`])
- **`intercept_resend.py`**: Simulates Eve measuring transiting qubits in random bases and resending collapsed states. Validated to reliably induce the theoretical ~25% QBER in BB84.
- **`mitm.py`**: Simulates Eve intercepting both quantum signals and public classical discussion. Demonstrates the critical difference between unauthenticated channels (succeeds with 0% QBER) and authenticated channels (blocked immediately).
- **`noise_channel.py`**: Configurable fiber depolarizing and bit-flip channel noise models.

### 3. Authentication & Key Distillation ([`quantum-auth-suite/auth/`] & [`postprocessing/`])
- **`wegman_carter.py`**: Information-theoretic classical authentication using polynomial evaluation over Mersenne prime $p = 2^{127}-1$.
- **`chsh_evaluator.py`**: Computes $S = E(a_1, b_1) - E(a_1, b_3) - E(a_3, b_1) + E(a_3, b_3)$. Validates $S \approx 2\sqrt{2} \approx 2.828 > 2.0$ for intact entanglement and $S \le 2.0$ under attack.
- **`privacy_amp.py`**: Parity reconciliation and Shannon privacy amplification to distill unconditionally secure secret keys.

### 4. Interactive Streamlit Interface ([`quantum-auth-suite/ui/`] & [`app.py`])
- **`views_simulator.py`**: Single Protocol Lab with step-by-step transmission logs, live metric cards, and Qiskit MPL circuit rendering.
- **`views_hybrid_auth.py`**: Interactive MitM playground demonstrating how classical authentication prevents man-in-the-middle attacks.
- **`views_theory.py`**: Theoretical academy with mathematical proofs and formulas.


## 🚀 How to Run the App

The Streamlit server is currently running in the background. You can open it in your browser:

```
http://localhost:8501
```

To run manually in a terminal at any time:
```bash
cd "c:\Users\yadav\Desktop\mini project\quantum-auth-suite"
streamlit run app.py
```
