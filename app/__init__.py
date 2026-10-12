"""
A Fully Async-based backend for Moerphous built using FastAPI,
ODMantic, MongoDB, IPFS, XRPL-PY and friends.
"""

__author__ = """Mahmoud Harmouch"""
__email__ = "business@wiseai.com"
__version__ = "0.1.0"


from app import (
    auth,
    wallets,
)

__all__ = [
    "auth",
    "wallets",
]
