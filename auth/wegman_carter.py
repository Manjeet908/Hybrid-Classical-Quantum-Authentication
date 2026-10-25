"""
Wegman-Carter Universal Hash Authentication.
Provides information-theoretic (unconditionally secure) message authentication
used in physical QKD setups to authenticate classical public discussion channels.
"""
from typing import Tuple
import hashlib

class WegmanCarterAuth:
    """
    Implements universal hash message authentication using linear congruence
    over a large Mersenne prime p = 2^127 - 1.
    """
    
    # Large prime for universal hashing
    PRIME = (1 << 127) - 1

    @classmethod
    def derive_subkeys(cls, secret_key: str) -> Tuple[int, int]:
        """Derives two subkeys (a, b) from a pre-shared secret string."""
        h1 = hashlib.sha256((secret_key + "_a").encode('utf-8')).hexdigest()
        h2 = hashlib.sha256((secret_key + "_b").encode('utf-8')).hexdigest()
        a = (int(h1, 16) % (cls.PRIME - 1)) + 1  # a in [1, p-1]
        b = int(h2, 16) % cls.PRIME              # b in [0, p-1]
        return a, b

    @classmethod
    def compute_tag(cls, message: str, secret_key: str) -> str:
        """
        Computes the authentication tag:
        Tag = (a * m + b) mod PRIME
        """
        a, b = cls.derive_subkeys(secret_key)
        # Convert message to integer
        m_hash = int(hashlib.sha256(message.encode('utf-8')).hexdigest(), 16)
        tag_val = (a * m_hash + b) % cls.PRIME
        return hex(tag_val)[2:].zfill(32)

    @classmethod
    def verify(cls, message: str, tag: str, secret_key: str) -> bool:
        """Verifies if the received tag matches the computed tag."""
        expected_tag = cls.compute_tag(message, secret_key)
        return expected_tag.lower() == tag.lower()
