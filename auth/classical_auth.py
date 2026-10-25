"""
Classical Authenticator for QKD public channels.
Supports both Wegman-Carter Universal Hashing and HMAC-SHA256 schemes.
"""
import hmac
import hashlib
from typing import Literal
from .wegman_carter import WegmanCarterAuth

AuthScheme = Literal["Wegman-Carter", "HMAC-SHA256"]

class ClassicalAuthenticator:
    """Manages classical authentication tags to secure the QKD public channel."""
    
    def __init__(self, scheme: AuthScheme = "Wegman-Carter"):
        self.scheme = scheme

    def generate_tag(self, message: str, secret_key: str) -> str:
        """Generates an authentication tag for the given message payload."""
        if self.scheme == "Wegman-Carter":
            return WegmanCarterAuth.compute_tag(message, secret_key)
        else:
            return hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

    def verify_tag(self, message: str, tag: str, secret_key: str) -> bool:
        """Verifies if the received message tag matches."""
        if self.scheme == "Wegman-Carter":
            return WegmanCarterAuth.verify(message, tag, secret_key)
        else:
            expected = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, tag)
