"""
app/blackbox/crypto.py — Military-Grade AES-256-GCM & 512-bit Container Encryption
==================================================================================
Implements binary packaging, key derivation, and authenticated encryption
for the .bbx (BlackBox) format.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct
from typing import Tuple, Dict, Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC_HEADER = b"UNIBBX01"
VERSION = 1
PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16
NONCE_SIZE = 12
SIG_SIZE = 64  # SHA-512


def derive_key(master_secret: bytes, salt: bytes) -> bytes:
    """Derives a 256-bit AES encryption key using PBKDF2 with SHA-512."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(master_secret)


def encrypt_container(payload_bytes: bytes, master_secret: bytes) -> bytes:
    """Encrypts a payload bytes into the .bbx binary container format.
    
    Structure:
      [0..8]   Magic (UNIBBX01)
      [8..10]  Version uint16
      [10..26] Salt (16 bytes)
      [26..38] Nonce (12 bytes)
      [38..46] Payload Length uint64
      [46..N]  Ciphertext + GCM Tag
      [N..N+64] HMAC-SHA512 Signature of entire packet
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    aes_key = derive_key(master_secret, salt)

    aesgcm = AESGCM(aes_key)
    # Additional authenticated data binds header metadata to ciphertext
    aad = MAGIC_HEADER + struct.pack(">HQ", VERSION, len(payload_bytes))
    ciphertext = aesgcm.encrypt(nonce, payload_bytes, aad)

    header = MAGIC_HEADER + struct.pack(">H", VERSION) + salt + nonce + struct.pack(">Q", len(payload_bytes))
    encrypted_body = header + ciphertext

    # Compute outer 512-bit HMAC signature
    h = hmac.new(master_secret, encrypted_body, hashlib.sha512)
    signature = h.digest()

    return encrypted_body + signature


def verify_container_integrity(container_bytes: bytes, master_secret: bytes) -> Tuple[bool, str]:
    """Verifies that the container has not been tampered with or modified."""
    if len(container_bytes) < len(MAGIC_HEADER) + 2 + SALT_SIZE + NONCE_SIZE + 8 + SIG_SIZE:
        return False, "Container is smaller than minimum header size"

    if not container_bytes.startswith(MAGIC_HEADER):
        return False, "Invalid container magic header (not a .bbx file)"

    data_to_verify = container_bytes[:-SIG_SIZE]
    expected_sig = container_bytes[-SIG_SIZE:]

    h = hmac.new(master_secret, data_to_verify, hashlib.sha512)
    calculated_sig = h.digest()

    if not hmac.compare_digest(expected_sig, calculated_sig):
        return False, "Cryptographic signature mismatch: container has been tampered with or corrupted!"

    return True, "Container signature verified (100% authentic)"


def decrypt_container(container_bytes: bytes, master_secret: bytes) -> bytes:
    """Decrypts a .bbx binary container strictly in memory.
    Raises ValueError on any tampering or incorrect key.
    """
    valid, msg = verify_container_integrity(container_bytes, master_secret)
    if not valid:
        raise ValueError(f"BlackBox Verification Failed: {msg}")

    # Parse header
    offset = len(MAGIC_HEADER)
    version = struct.unpack(">H", container_bytes[offset:offset+2])[0]
    offset += 2

    if version != VERSION:
        raise ValueError(f"Unsupported BlackBox container version: {version}")

    salt = container_bytes[offset:offset+SALT_SIZE]
    offset += SALT_SIZE

    nonce = container_bytes[offset:offset+NONCE_SIZE]
    offset += NONCE_SIZE

    payload_len = struct.unpack(">Q", container_bytes[offset:offset+8])[0]
    offset += 8

    ciphertext = container_bytes[offset:-SIG_SIZE]

    # Derive key and decrypt
    aes_key = derive_key(master_secret, salt)
    aesgcm = AESGCM(aes_key)
    aad = MAGIC_HEADER + struct.pack(">HQ", version, payload_len)

    try:
        decrypted = aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as e:
        raise ValueError(f"AES-256-GCM decryption failed (corrupted ciphertext or invalid key): {e}")

    if len(decrypted) != payload_len:
        raise ValueError(f"Payload length mismatch: expected {payload_len}, got {len(decrypted)}")

    return decrypted
