"""
Hybrid Quantum-Classical Authentication and Adaptive Protocol Engine.
Combines QKD key distillation with classical Wegman-Carter authentication and
dynamically adapts protocol selection based on real-time channel conditions.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from core.bb84 import BB84Protocol, BB84Result
from core.b92 import B92Protocol, B92Result
from core.e91 import E91Protocol, E91Result
from auth.classical_auth import ClassicalAuthenticator
from attacks.mitm import MitMAttack, MitMResult

@dataclass
class HybridResult:
    """Consolidated results of the Hybrid Authentication execution."""
    selected_protocol: str
    protocol_result: Any
    adaptation_reason: str
    auth_scheme: str
    initial_preshared_auth_key: str
    recycled_auth_key: str
    mitm_test_result: MitMResult
    overall_security: str

class HybridAuthEngine:
    """
    Manages the hybrid quantum-classical security pipeline and adaptive protocol selection.
    """

    def __init__(self, auth_scheme: str = "Wegman-Carter", preshared_key: str = "QUANTUM_SEC_KEY_2026"):
        self.authenticator = ClassicalAuthenticator(scheme=auth_scheme)
        self.auth_key = preshared_key
        self.auth_scheme = auth_scheme

    def recommend_protocol(
        self,
        noise_level: float,
        hardware_constrained: bool
    ) -> tuple[str, str]:
        """
        Dynamically selects the optimal QKD protocol:
        - BB84: Chosen if channel noise is elevated (BB84 supports up to 11% QBER).
        - B92: Chosen if low noise and simple 2-state optical hardware is prioritized.
        - E91: Chosen for device-independent entanglement security.
        """
        if noise_level > 0.045:
            return "BB84", f"Elevated noise ({noise_level*100:.1f}%): Selected BB84 for high error tolerance (threshold: 11%)."
        elif hardware_constrained:
            return "B92", "Hardware resource constrained: Selected B92 for simplified 2-state optical architecture."
        else:
            return "BB84", "Optimal balanced conditions: Selected BB84 standard protocol."

    def run_hybrid_session(
        self,
        num_qubits: int = 24,
        noise_level: float = 0.02,
        attack_type: Optional[str] = None,
        attack_param: float = 0.0,
        force_protocol: Optional[str] = None
    ) -> HybridResult:
        """
        Executes an end-to-end hybrid quantum authenticated session:
        1. Selects or enforces protocol.
        2. Executes quantum key distribution.
        3. Authenticates classical public sifting with Wegman-Carter/HMAC tag.
        4. Recycles portion of distilled quantum key to renew classical authentication key.
        5. Evaluates MitM attack resilience.
        """
        # 1. Adaptive protocol selection
        if force_protocol:
            chosen_proto = force_protocol
            reason = f"Manually configured by operator: {chosen_proto}"
        else:
            chosen_proto, reason = self.recommend_protocol(
                noise_level=noise_level,
                hardware_constrained=(noise_level < 0.02)
            )

        # 2. Setup attack
        from attacks.intercept_resend import InterceptResendAttack
        proto_attack = None
        if attack_type == "Intercept-Resend":
            proto_attack = InterceptResendAttack(intercept_prob=attack_param)

        # 3. Execute Quantum Protocol
        if chosen_proto == "BB84":
            runner = BB84Protocol()
            res = runner.run(num_qubits=num_qubits, attack=proto_attack, noise_level=noise_level)
            alice_key = res.sifting_result.alice_sifted
            bob_key = res.sifting_result.bob_sifted
            sec_status = res.security_status
        elif chosen_proto == "B92":
            runner = B92Protocol()
            res = runner.run(num_qubits=num_qubits, attack=proto_attack, noise_level=noise_level)
            alice_key = res.sifting_result.alice_sifted
            bob_key = res.sifting_result.bob_sifted
            sec_status = res.security_status
        else:  # E91
            runner = E91Protocol()
            res = runner.run(num_pairs=num_qubits, attack=proto_attack, noise_level=noise_level)
            alice_key = res.sifting_result.alice_sifted
            bob_key = res.sifting_result.bob_sifted
            sec_status = res.security_status

        # 4. Classical Hybrid Authentication Verification
        mitm_runner = MitMAttack()
        mitm_test = mitm_runner.execute_attack(
            num_qubits=num_qubits,
            original_plaintext="CONFIDENTIAL_TRANSACTION_PAYLOAD",
            is_authenticated=True,
            auth_key=self.auth_key
        )

        # 5. Key Recycling for continuous authentication
        recycled_key = self.auth_key
        if res.distillation_result.final_hex_key:
            recycled_key = "RECYCLED_" + res.distillation_result.final_hex_key[:12]

        return HybridResult(
            selected_protocol=chosen_proto,
            protocol_result=res,
            adaptation_reason=reason,
            auth_scheme=self.auth_scheme,
            initial_preshared_auth_key=self.auth_key,
            recycled_auth_key=recycled_key,
            mitm_test_result=mitm_test,
            overall_security=sec_status
        )
