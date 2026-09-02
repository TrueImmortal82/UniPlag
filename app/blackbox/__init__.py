"""
app/blackbox — UniPlag & ICG Anti-Decompilation & Encrypted Distribution Subsystem
================================================================================
Provides:
  - Cryptographic container format (.bbx) with AES-256-GCM and HMAC-SHA512 seal.
  - Zero-Disk in-memory execution engine (RAM-only module and asset loader).
  - Anti-debugging and process integrity verification.
"""

from .crypto import encrypt_container, decrypt_container, verify_container_integrity
from .loader import mount_in_memory_container
from .antidebug import check_debugger_present

__all__ = [
    "encrypt_container",
    "decrypt_container",
    "verify_container_integrity",
    "mount_in_memory_container",
    "check_debugger_present",
]
