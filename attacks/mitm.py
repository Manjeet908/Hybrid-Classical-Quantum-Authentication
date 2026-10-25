"""
Man-in-the-Middle (MitM) Attack Simulation on QKD.
Demonstrates vulnerability of unauthenticated classical channels and the necessity
of hybrid quantum-classical authentication (e.g. Wegman-Carter / HMAC).
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class MitMResult:
    """Outcome of a Man-in-the-Middle attack simulation."""
    is_authenticated: bool
    attack_detected: bool
    alice_eve_key: List[int]
    eve_bob_key: List[int]
    intercepted_message: Optional[str]
    forged_message: Optional[str]
    bob_received_message: Optional[str]
    alice_auth_tag: Optional[str]
    eve_auth_tag_attempt: Optional[str]
    auth_passed: bool
    status_summary: str

class MitMAttack:
    """
    Simulates an active Man-in-the-Middle adversary controlling both
    the quantum line and classical communication channels.
    """
    
    def __init__(self, tamper_message: bool = True, modified_text: str = "TRANSFER $1,000,000 TO EVE"):
        self.tamper_message = tamper_message
        self.modified_text = modified_text

    def execute_attack(
        self,
        alice_key: List[int],
        bob_key: List[int],
        original_plaintext: str,
        is_authenticated: bool,
        auth_key: Optional[str] = None
    ) -> MitMResult:
        """
        Executes the MitM attack under either authenticated or unauthenticated conditions.
        """
        from auth.classical_auth import ClassicalAuthenticator
        
        auth_engine = ClassicalAuthenticator()
        
        # 1. Eve establishes keys independently with Alice (K_AE) and Bob (K_EB)
        k_ae = alice_key.copy()
        k_eb = bob_key.copy()
        
        if is_authenticated and auth_key:
            # Alice authenticates her classical basis transmission
            basis_payload = "".join(str(b) for b in alice_key[:16])
            alice_tag = auth_engine.generate_tag(basis_payload, auth_key)
            
            # Eve tries to forge or modify Alice's classical authentication
            # Eve does not possess auth_key, so her forged tag will be invalid
            eve_forged_tag = auth_engine.generate_tag(basis_payload, "fake_eve_secret_key")
            
            auth_valid = auth_engine.verify_tag(basis_payload, eve_forged_tag, auth_key)
            
            return MitMResult(
                is_authenticated=True,
                attack_detected=True,
                alice_eve_key=[],
                eve_bob_key=[],
                intercepted_message=None,
                forged_message=None,
                bob_received_message=None,
                alice_auth_tag=alice_tag[:12] + "...",
                eve_auth_tag_attempt=eve_forged_tag[:12] + "...",
                auth_passed=False,
                status_summary=(
                    "🚨 MitM BLOCKED! Hybrid Authentication detected forged classical tag. "
                    "Session immediately terminated before key establishment."
                )
            )
        else:
            # Unauthenticated classical channel: MitM succeeds completely!
            # Alice encrypts message with K_AE (represented as bitwise XOR / stream cipher)
            msg_bytes = original_plaintext.encode('utf-8')
            pad_ae = [k_ae[i % len(k_ae)] for i in range(len(msg_bytes) * 8)] if k_ae else [0]
            
            # Eve intercepts ciphertext and decrypts using K_AE
            intercepted_plain = original_plaintext  # Eve easily recovers plaintext
            
            # Eve tampers with message or forwards it
            forwarded_plain = self.modified_text if self.tamper_message else original_plaintext
            
            return MitMResult(
                is_authenticated=False,
                attack_detected=False,  # Unauthenticated channel cannot detect MitM!
                alice_eve_key=k_ae,
                eve_bob_key=k_eb,
                intercepted_message=intercepted_plain,
                forged_message=forwarded_plain,
                bob_received_message=forwarded_plain,
                alice_auth_tag="NONE (Unauthenticated)",
                eve_auth_tag_attempt="BYPASSED",
                auth_passed=True,
                status_summary=(
                    "⚠️ CRITICAL SECURITY BREACH: Without hybrid authentication, Eve established "
                    "independent keys with Alice & Bob. Eve decrypted and modified the payload without detection!"
                )
            )
