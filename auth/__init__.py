"""
Hybrid Classical-Quantum Authentication Modules.
"""
from .wegman_carter import WegmanCarterAuth
from .classical_auth import ClassicalAuthenticator

__all__ = ["WegmanCarterAuth", "ClassicalAuthenticator"]
