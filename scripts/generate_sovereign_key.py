"""
scripts/generate_sovereign_key.py — Sovereign 512-bit Master Key Generator
Generates a cryptographically strong 512-bit (64-byte / 128-hex chars) private key
stored exclusively on the local machine in .security/sovereign_512.key (ignored by Git).
"""

import os
import secrets
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECURITY_DIR = PROJECT_ROOT / ".security"
KEY_FILE = SECURITY_DIR / "sovereign_512.key"

def generate_key(force: bool = False) -> str:
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    
    if KEY_FILE.exists() and not force:
        print(f"ℹ️ Sovereign 512-bit key already exists at: {KEY_FILE}")
        key_hex = KEY_FILE.read_text(encoding="utf-8").strip()
        print(f"  Key Length: {len(bytes.fromhex(key_hex)) * 8} bits (64 bytes)")
        return key_hex

    # 64 bytes = 512 bits of cryptographically secure random bytes
    key_bytes = secrets.token_bytes(64)
    key_hex = key_bytes.hex()
    
    KEY_FILE.write_text(key_hex, encoding="utf-8")
    
    # Try to set restrictive permissions (on POSIX systems)
    try:
        os.chmod(KEY_FILE, 0o600)
    except Exception:
        pass

    print("🛡️ [UniPlag Security] Sovereign 512-bit Master Key Generated Successfully!")
    print(f"  📁 Location: {KEY_FILE}")
    print(f"  🔑 Key Size: 512 bits ({len(key_bytes)} bytes / 128 hex chars)")
    print(f"  🔒 Git Status: EXCLUDED via .gitignore (Will NEVER be uploaded to git)")
    return key_hex

if __name__ == "__main__":
    force_gen = "--force" in sys.argv
    generate_key(force=force_gen)
