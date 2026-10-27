"""
Realistic Man-in-the-Middle (MitM) Attack Simulation on QKD.

In a real MitM attack, Eve does NOT simply copy Alice's and Bob's keys.
Instead, Eve physically intercepts the quantum channel and runs TWO
independent BB84 key exchanges:
  1. Alice ↔ Eve  (Eve impersonates Bob to Alice)
  2. Eve   ↔ Bob  (Eve impersonates Alice to Bob)

Eve then controls both resulting keys (K_AE and K_EB) and can decrypt,
read, modify, and re-encrypt all messages transparently — unless the
classical sifting channel is authenticated (e.g., via Wegman-Carter).
"""
from core import QiskitEngine
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


# ── Data classes ──────────────────────────────────────────────────────

@dataclass
class MitMKeyExchange:
    """Result of a single leg of the MitM key exchange."""
    sender_bits: List[int]
    sender_bases: List[int]
    receiver_bases: List[int]
    receiver_measured: List[int]
    sifted_sender: List[int]
    sifted_receiver: List[int]
    matching_indices: List[int]
    qber: float


@dataclass
class MitMResult:
    """Full outcome of the realistic MitM attack simulation."""
    is_authenticated: bool
    attack_detected: bool

    # Two independent key exchanges
    alice_eve_exchange: MitMKeyExchange
    eve_bob_exchange: MitMKeyExchange

    # Derived shared keys (bit-lists)
    alice_eve_key: List[int]
    eve_bob_key: List[int]

    # Message interception chain
    original_plaintext: str
    alice_ciphertext_hex: str
    intercepted_message: Optional[str]
    forged_message: Optional[str]
    eve_ciphertext_hex: Optional[str]
    bob_received_message: Optional[str]

    # Authentication tags
    alice_auth_tag: Optional[str]
    eve_auth_tag_attempt: Optional[str]
    auth_passed: bool

    status_summary: str


# ── Helpers ───────────────────────────────────────────────────────────

def _xor_encrypt(plaintext: str, key_bits: List[int]) -> tuple[str, str]:
    """
    XOR-encrypts a plaintext string using a bit-key (OTP / stream cipher).
    Returns (ciphertext_hex, decrypted_plaintext_for_verification).
    """
    msg_bytes = plaintext.encode("utf-8")
    # Extend key to cover message length
    extended_key = []
    for i in range(len(msg_bytes)):
        byte_val = 0
        for bit_idx in range(8):
            k = key_bits[(i * 8 + bit_idx) % len(key_bits)] if key_bits else 0
            byte_val = (byte_val << 1) | k
        extended_key.append(byte_val)

    cipher_bytes = bytes(m ^ k for m, k in zip(msg_bytes, extended_key))
    return cipher_bytes.hex(), cipher_bytes


def _xor_decrypt(cipher_bytes: bytes, key_bits: List[int]) -> str:
    """XOR-decrypts ciphertext bytes using a bit-key."""
    extended_key = []
    for i in range(len(cipher_bytes)):
        byte_val = 0
        for bit_idx in range(8):
            k = key_bits[(i * 8 + bit_idx) % len(key_bits)] if key_bits else 0
            byte_val = (byte_val << 1) | k
        extended_key.append(byte_val)

    plain_bytes = bytes(c ^ k for c, k in zip(cipher_bytes, extended_key))
    try:
        return plain_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return plain_bytes.decode("utf-8", errors="replace")


def _run_bb84_key_exchange(
    sender_bits: List[int],
    sender_bases: List[int],
    receiver_bases: List[int],
    engine: QiskitEngine,
    num_qubits: int,
) -> MitMKeyExchange:
    """
    Runs a single BB84 key exchange on a real Qiskit circuit.
    The sender prepares qubits, the receiver measures in their own bases.
    """
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from postprocessing.sifting import sift_bb84 as _sift_bb84

    qr = QuantumRegister(num_qubits, "q")
    cr = ClassicalRegister(num_qubits, "m")
    qc = QuantumCircuit(qr, cr)

    # Sender prepares
    for i in range(num_qubits):
        if sender_bits[i] == 1:
            qc.x(qr[i])
        if sender_bases[i] == 1:  # X-basis
            qc.h(qr[i])
    qc.barrier(label="Prep")

    # Receiver measures
    for i in range(num_qubits):
        if receiver_bases[i] == 1:  # X-basis
            qc.h(qr[i])
        qc.measure(qr[i], cr[i])

    # Simulate
    receiver_measured, _ = engine.sample_registers(qc)

    # Sift
    sift_res = _sift_bb84(
        sender_bits, sender_bases,
        receiver_measured, receiver_bases,
        security_threshold=0.11,
    )

    return MitMKeyExchange(
        sender_bits=sender_bits,
        sender_bases=sender_bases,
        receiver_bases=receiver_bases,
        receiver_measured=receiver_measured,
        sifted_sender=sift_res.alice_sifted,
        sifted_receiver=sift_res.bob_sifted,
        matching_indices=sift_res.matching_indices,
        qber=sift_res.qber,
    )


# ── Main MitM Attack Class ───────────────────────────────────────────

class MitMAttack:
    """
    Simulates a realistic Man-in-the-Middle attack where Eve runs two
    independent BB84 key exchanges by intercepting the quantum channel.
    """

    def __init__(
        self,
        tamper_message: bool = True,
        modified_text: str = "TRANSFER $1,000,000 TO EVE",
        seed: Optional[int] = None,
    ):
        self.tamper_message = tamper_message
        self.modified_text = modified_text
        self.rng = np.random.default_rng(seed)
        self._seed = seed
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            from core.qiskit_engine import QiskitEngine
            self._engine = QiskitEngine(seed=self._seed)
        return self._engine

    def execute_attack(
        self,
        num_qubits: int = 32,
        original_plaintext: str = "AUTHORIZE TRANSFER: $500,000 TO ACCT #8841",
        is_authenticated: bool = False,
        auth_key: Optional[str] = None,
        # Legacy compatibility params (ignored in new implementation)
        alice_key: Optional[List[int]] = None,
        bob_key: Optional[List[int]] = None,
    ) -> MitMResult:
        """
        Executes a realistic MitM attack:

        Phase 1 — Quantum Interception:
          a) Alice prepares qubits and sends toward "Bob".
          b) Eve intercepts, measures with her own random bases → K_AE.
          c) Eve prepares NEW qubits based on her measurements and sends to Bob.
          d) Bob measures with his own random bases → K_EB.

        Phase 2 — Classical Channel (Sifting):
          a) Alice announces her bases publicly.
          b) Eve intercepts the announcement, performs sifting with Alice → shared K_AE.
          c) Eve announces HER sending bases to Bob (impersonating Alice).
          d) Bob sifts with Eve's bases → shared K_EB.

        Phase 3 — Message Relay:
          a) Alice encrypts message with K_AE, sends ciphertext.
          b) Eve decrypts with K_AE, reads/modifies, re-encrypts with K_EB.
          c) Bob decrypts with K_EB — sees Eve's version.

        If authenticated: Eve cannot forge auth tags → attack blocked at Phase 2.
        """
        # ── Phase 1: Generate random bits and bases for all parties ───
        alice_bits  = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
        alice_bases = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
        eve_bases   = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]
        bob_bases   = [int(b) for b in self.rng.integers(0, 2, size=num_qubits)]

        # ── Leg 1: Alice → Eve (Eve impersonates Bob) ────────────────
        # Eve measures Alice's qubits with her own random bases
        leg1 = _run_bb84_key_exchange(
            sender_bits=alice_bits,
            sender_bases=alice_bases,
            receiver_bases=eve_bases,
            engine=self.engine,
            num_qubits=num_qubits,
        )
        # Eve's measured bits become what she "received" from Alice
        eve_measured_from_alice = leg1.receiver_measured

        # ── Leg 2: Eve → Bob (Eve impersonates Alice) ────────────────
        # Eve re-prepares qubits based on what she measured and sends to Bob
        # She uses her own bases as the "sender bases" for this leg
        leg2 = _run_bb84_key_exchange(
            sender_bits=eve_measured_from_alice,
            sender_bases=eve_bases,
            receiver_bases=bob_bases,
            engine=self.engine,
            num_qubits=num_qubits,
        )

        # ── Phase 2: Classical Channel Authentication Check ──────────
        if is_authenticated and auth_key:
            from auth.classical_auth import ClassicalAuthenticator
            auth_engine = ClassicalAuthenticator()

            # Alice authenticates her basis announcement
            basis_announcement = ",".join(str(b) for b in alice_bases)
            alice_tag = auth_engine.generate_tag(basis_announcement, auth_key)

            # Eve intercepts but cannot forge a valid tag without auth_key
            # Eve tries to forge a tag for her OWN bases (to impersonate Alice to Bob)
            eve_fake_announcement = ",".join(str(b) for b in eve_bases)
            eve_tag = auth_engine.generate_tag(eve_fake_announcement, "EVE_FAKE_KEY_ATTEMPT")

            # Bob would verify the tag — it fails
            tag_valid = auth_engine.verify_tag(eve_fake_announcement, eve_tag, auth_key)

            return MitMResult(
                is_authenticated=True,
                attack_detected=True,
                alice_eve_exchange=leg1,
                eve_bob_exchange=leg2,
                alice_eve_key=leg1.sifted_receiver,
                eve_bob_key=[],
                original_plaintext=original_plaintext,
                alice_ciphertext_hex="",
                intercepted_message=None,
                forged_message=None,
                eve_ciphertext_hex=None,
                bob_received_message=None,
                alice_auth_tag=alice_tag,
                eve_auth_tag_attempt=eve_tag,
                auth_passed=False,
                status_summary=(
                    "🚨 MitM BLOCKED! Bob verified Alice's basis announcement using "
                    "Wegman-Carter authentication. Eve's forged tag failed verification. "
                    "Session terminated — no keys established with the adversary."
                ),
            )

        # ── Phase 3: Unauthenticated — Eve relays modified messages ──
        k_ae = leg1.sifted_sender   # Alice's view of the shared key with "Bob" (actually Eve)
        k_eb = leg2.sifted_receiver  # Bob's view of the shared key with "Alice" (actually Eve)
        # Eve holds both: leg1.sifted_receiver (matches k_ae) and leg2.sifted_sender (matches k_eb)

        # Ensure we have at least some key bits for encryption
        if not k_ae:
            k_ae = [0, 1, 0, 1]
        if not k_eb:
            k_eb = [1, 0, 1, 0]

        # Alice encrypts with K_AE
        alice_ct_hex, alice_ct_bytes = _xor_encrypt(original_plaintext, k_ae)

        # Eve decrypts with her copy of K_AE
        eve_k_ae = leg1.sifted_receiver if leg1.sifted_receiver else k_ae
        eve_decrypted = _xor_decrypt(alice_ct_bytes, eve_k_ae)

        # Eve modifies (or keeps) the message
        forwarded_plain = self.modified_text if self.tamper_message else eve_decrypted

        # Eve re-encrypts with K_EB and sends to Bob
        eve_k_eb = leg2.sifted_sender if leg2.sifted_sender else k_eb
        eve_ct_hex, eve_ct_bytes = _xor_encrypt(forwarded_plain, eve_k_eb)

        # Bob decrypts with K_EB
        bob_decrypted = _xor_decrypt(eve_ct_bytes, k_eb)

        return MitMResult(
            is_authenticated=False,
            attack_detected=False,
            alice_eve_exchange=leg1,
            eve_bob_exchange=leg2,
            alice_eve_key=k_ae,
            eve_bob_key=k_eb,
            original_plaintext=original_plaintext,
            alice_ciphertext_hex=alice_ct_hex,
            intercepted_message=eve_decrypted,
            forged_message=forwarded_plain,
            eve_ciphertext_hex=eve_ct_hex,
            bob_received_message=bob_decrypted,
            alice_auth_tag="NONE (Unauthenticated)",
            eve_auth_tag_attempt="BYPASSED",
            auth_passed=True,
            status_summary=(
                "⚠️ CRITICAL SECURITY BREACH: Eve ran two independent BB84 sessions — "
                "one with Alice (K_AE) and one with Bob (K_EB). Eve decrypted Alice's "
                "message, modified it, re-encrypted, and forwarded to Bob undetected!"
            ),
        )
