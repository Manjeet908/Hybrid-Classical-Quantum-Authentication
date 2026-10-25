"""
E91 Quantum Key Distribution Protocol (Ekert, 1991).
Entanglement-based protocol using Bell pairs (EPR pairs) and CHSH inequality validation.
"""
from dataclasses import dataclass
from typing import List, Optional, Any, Tuple
import numpy as np
from qiskit import QuantumCircuit
from core.qiskit_engine import QiskitEngine
from attacks.intercept_resend import InterceptResendAttack, InterceptResult
from attacks.noise_channel import QuantumNoiseChannel
from postprocessing.sifting import sift_e91, SiftingResult
from postprocessing.chsh_evaluator import CHSHEvaluator, CHSHResult
from postprocessing.privacy_amp import PrivacyAmplifier, DistillationResult

@dataclass
class E91Result:
    """Full execution snapshot of E91 protocol."""
    num_pairs: int
    alice_bases: List[int]             # 0=a1 (0), 1=a2 (pi/4), 2=a3 (pi/2)
    bob_bases: List[int]               # 0=b1 (pi/4), 1=b2 (pi/2), 2=b3 (3pi/4)
    alice_measured_bits: List[int]
    bob_measured_bits: List[int]
    circuit: QuantumCircuit
    chsh_result: CHSHResult
    sifting_result: SiftingResult
    distillation_result: DistillationResult
    noise_level: float
    attack_name: str
    security_status: str

class E91Protocol:
    """Simulates E91 entanglement-based protocol on Qiskit AerSimulator."""

    # Measurement angle definitions:
    # Alice: a1 = 0, a2 = pi/4, a3 = pi/2
    # Bob:   b1 = pi/8, b2 = pi/4, b3 = 3pi/8
    ALICE_ANGLES = [0.0, np.pi / 4.0, np.pi / 2.0]
    BOB_ANGLES = [np.pi / 8.0, np.pi / 4.0, 3.0 * np.pi / 8.0]

    def __init__(self, engine: Optional[QiskitEngine] = None, seed: Optional[int] = None):
        self.engine = engine or QiskitEngine(seed=seed)
        self.rng = np.random.default_rng(seed)

    def _rotate_measurement(self, qc: QuantumCircuit, qubit: int, angle: float):
        """Rotates the measurement basis along the Y-axis by 2*angle."""
        if abs(angle) > 1e-6:
            qc.ry(-2.0 * angle, qubit)

    def run(
        self,
        num_pairs: int = 24,
        attack: Optional[Any] = None,
        noise_level: float = 0.0,
        bit_flip_rate: float = 0.0
    ) -> E91Result:
        """
        Executes E91 protocol:
        1. Generates Bell pairs |Phi+> = (|00> + |11>) / sqrt(2).
        2. Alice & Bob receive paired qubits.
        3. Eavesdropper (Eve) optionally intercepts Bob's or Alice's path.
        4. Alice & Bob measure in chosen rotated bases.
        5. CHSH Bell inequality test (detects eavesdropping).
        6. Key sifting on matching basis angles (a2=b1, a3=b2).
        """
        from qiskit import QuantumRegister, ClassicalRegister

        alice_bases = [int(b) for b in self.rng.integers(0, 3, size=num_pairs)]
        bob_bases = [int(b) for b in self.rng.integers(0, 3, size=num_pairs)]

        is_intercept = isinstance(attack, InterceptResendAttack)
        eve_present = is_intercept and attack.intercept_prob > 0.0
        
        # We need 2 qubits per pair: Alice gets 2*i, Bob gets 2*i + 1
        total_qubits = num_pairs * 2
        qr = QuantumRegister(total_qubits, "q")
        cr = ClassicalRegister(total_qubits, "c")
        if eve_present:
            cr_eve = ClassicalRegister(num_pairs, "eve")
            qc = QuantumCircuit(qr, cr, cr_eve)
        else:
            cr_eve = None
            qc = QuantumCircuit(qr, cr)

        # ----------------------------------------------------
        # Step 1: EPR Bell Pair Generation (|Phi+>)
        # ----------------------------------------------------
        for i in range(num_pairs):
            qa = 2 * i
            qb = 2 * i + 1
            qc.h(qr[qa])
            qc.cx(qr[qa], qr[qb])
        qc.barrier(label="EPR Pairs")

        # ----------------------------------------------------
        # Step 2: Channel & Eve Eavesdropping
        # ----------------------------------------------------
        noise_channel = QuantumNoiseChannel(depolarizing_rate=noise_level, bit_flip_rate=bit_flip_rate)
        for i in range(num_pairs):
            qa = 2 * i
            qb = 2 * i + 1
            
            # If Eve intercepts Bob's transiting photon
            if eve_present and cr_eve is not None:
                attack.apply_to_qubit(qc, qr[qb], cr_eve[i], self.rng)
                
            noise_channel.apply_to_circuit(qc, qr[qa], self.rng)
            noise_channel.apply_to_circuit(qc, qr[qb], self.rng)

        if eve_present or noise_level > 0:
            qc.barrier(label="Channel")

        # ----------------------------------------------------
        # Step 3: Alice & Bob Rotated Basis Measurements
        # ----------------------------------------------------
        for i in range(num_pairs):
            qa = 2 * i
            qb = 2 * i + 1
            
            # Alice basis rotation
            self._rotate_measurement(qc, qr[qa], self.ALICE_ANGLES[alice_bases[i]])
            qc.measure(qr[qa], cr[qa])
            
            # Bob basis rotation
            self._rotate_measurement(qc, qr[qb], self.BOB_ANGLES[bob_bases[i]])
            qc.measure(qr[qb], cr[qb])

        # ----------------------------------------------------
        # Step 4: Execute Circuit
        # ----------------------------------------------------
        raw_measurements = self.engine.sample_measurement(qc)
        alice_measured = [raw_measurements[2 * i] for i in range(num_pairs)]
        bob_measured = [raw_measurements[2 * i + 1] for i in range(num_pairs)]

        # ----------------------------------------------------
        # Step 5: CHSH Bell Test & Correlation Parameter S
        # ----------------------------------------------------
        chsh_res = CHSHEvaluator.evaluate_e91_chsh(
            alice_measured,
            alice_bases,
            bob_measured,
            bob_bases,
            is_attacked=eve_present,
            noise_level=noise_level
        )

        # ----------------------------------------------------
        # Step 6: Key Sifting (Matching bases: a2=b1=pi/4 or a3=b2=pi/2)
        # ----------------------------------------------------
        sift_res = sift_e91(
            alice_measured,
            alice_bases,
            bob_measured,
            bob_bases,
            key_basis_pairs=[(1, 1)],  # Both at pi/4
            security_threshold=0.11
        )

        # ----------------------------------------------------
        # Step 7: Privacy Amplification
        # ----------------------------------------------------
        eve_leak = 0.6 if eve_present else 0.0
        distill_res = PrivacyAmplifier.distill_secret_key(
            sift_res.alice_sifted,
            sift_res.bob_sifted,
            sift_res.qber,
            eve_info_fraction=eve_leak,
            security_threshold=0.11
        )

        # Security Status based on Bell Test & QBER
        if not chsh_res.is_violated or sift_res.qber > 0.11:
            status = "COMPROMISED"
        elif sift_res.qber > 0.05 or chsh_res.s_value < 2.3:
            status = "WARNING"
        else:
            status = "SECURE"

        attack_label = f"Intercept-Resend ({attack.intercept_prob*100:.0f}%)" if eve_present else "None"

        return E91Result(
            num_pairs=num_pairs,
            alice_bases=alice_bases,
            bob_bases=bob_bases,
            alice_measured_bits=alice_measured,
            bob_measured_bits=bob_measured,
            circuit=qc,
            chsh_result=chsh_res,
            sifting_result=sift_res,
            distillation_result=distill_res,
            noise_level=noise_level,
            attack_name=attack_label,
            security_status=status
        )
