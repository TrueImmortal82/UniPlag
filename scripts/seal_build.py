"""
scripts/seal_build.py — UniPlag & ICG Official Build Sealer CLI
Scans all protected code files, computes canonical SHA-256 hashes, signs with HMAC-SHA256,
and writes .integrity_manifest.json.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.integrity import generate_and_save_manifest, verify_code_integrity

def main():
    print("🔒 [UniPlag Anti-Tamper] Sealing Codebase Build...")
    manifest = generate_and_save_manifest()
    print(f"  ✅ Protected Files Count: {manifest['file_count']}")
    print(f"  ✅ HMAC-SHA256 Signature: {manifest['signature']}")
    print(f"  ✅ Manifest File: .integrity_manifest.json")
    
    # Verification check
    res = verify_code_integrity()
    if res.is_valid:
        print("  🎉 Integrity verification: 100% VALID & SEALED.")
    else:
        print(f"  ⚠️ Warning during verification: {res.details}")

if __name__ == "__main__":
    main()
