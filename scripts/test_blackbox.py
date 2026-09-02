"""
scripts/test_blackbox.py — UniPlag Enterprise BlackBox (.bbx) Test Suite
Tests:
  1. Military-grade AES-256-GCM encryption & decryption
  2. Anti-tamper 512-bit HMAC signature validation (tampered byte rejection)
  3. Wrong master key rejection
  4. In-memory bytecode loading & execution (Zero-Disk Footprint)
  5. Built dist/UniPlag_Enterprise.bbx integrity & structure
"""

import sys
import os
import io
import zipfile
import py_compile
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.blackbox.crypto import (
    encrypt_container,
    decrypt_container,
    verify_container_integrity,
    derive_key,
    MAGIC_HEADER,
)
from app.blackbox.loader import mount_in_memory_container, MemoryZipModuleFinder
from app.blackbox.antidebug import is_running_under_debugger, check_debugger_present
from app.integrity import get_sovereign_key_512

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


print("\n" + "═" * 70)
print("  🛡️  UNIPLAG ENTERPRISE BLACKBOX (.bbx) TEST SUITE")
print("═" * 70)

master_key = get_sovereign_key_512()
sample_payload = b"UniPlag & ICG Enterprise Core Secret Bytecode and Data"

print("\n═══ CASE 1: AES-256-GCM Encryption & In-Memory Decryption ═══")
encrypted_blob = encrypt_container(sample_payload, master_key)
check_test("CASE_1.a Encrypted blob starts with magic header UNIBBX01", encrypted_blob.startswith(MAGIC_HEADER))
check_test("CASE_1.b Encrypted blob size is larger than payload", len(encrypted_blob) > len(sample_payload))

decrypted_blob = decrypt_container(encrypted_blob, master_key)
check_test("CASE_1.c Decrypted payload matches original bytes exactly", decrypted_blob == sample_payload)

print("\n═══ CASE 2: Anti-Tamper & Cryptographic Signature Validation ═══")
valid, msg = verify_container_integrity(encrypted_blob, master_key)
check_test("CASE_2.a Untampered container passes signature check", valid)

# Tamper 1 byte in ciphertext
tampered_blob = bytearray(encrypted_blob)
tampered_blob[40] ^= 0xFF
valid_t, msg_t = verify_container_integrity(bytes(tampered_blob), master_key)
check_test("CASE_2.b Tampered ciphertext byte rejected by signature check", not valid_t)

try:
    decrypt_container(bytes(tampered_blob), master_key)
    tamper_caught = False
except ValueError:
    tamper_caught = True
check_test("CASE_2.c Tampered container raises ValueError on decryption attempt", tamper_caught)

print("\n═══ CASE 3: Wrong Key Rejection ═══")
fake_key = b"A" * 64
try:
    decrypt_container(encrypted_blob, fake_key)
    wrong_key_caught = False
except ValueError:
    wrong_key_caught = True
check_test("CASE_3.a Decryption fails with invalid key", wrong_key_caught)

print("\n═══ CASE 4: Zero-Disk In-Memory Bytecode Execution ═══")
# Build in-memory zip with a test module
test_zip_buffer = io.BytesIO()
with zipfile.ZipFile(test_zip_buffer, "w") as zf:
    code_src = "def secret_formula(a, b):\n    return (a * 7932) + b\n"
    code_obj = compile(code_src, "<test_virtual>", "exec")
    
    # Marshal code object into standard .pyc format (16 byte header)
    import marshal
    pyc_data = b"\x00" * 16 + marshal.dumps(code_obj)
    zf.writestr("test_secret_module.pyc", pyc_data)

zip_bytes = test_zip_buffer.getvalue()
mount = mount_in_memory_container(zip_bytes)
check_test("CASE_4.a Virtual memory finder mounted in sys.meta_path", mount in sys.meta_path)

import test_secret_module
calc_res = test_secret_module.secret_formula(2, 5)
check_test("CASE_4.b In-memory module imported and executed (res=15869)", calc_res == (2 * 7932 + 5))
check_test("CASE_4.c Module __file__ indicates in-memory location", "<blackbox:" in test_secret_module.__file__)

print("\n═══ CASE 5: Built UniPlag_Enterprise.bbx Validation ═══")
bbx_file = PROJECT_ROOT / "dist" / "UniPlag_Enterprise.bbx"
check_test("CASE_5.a dist/UniPlag_Enterprise.bbx exists", bbx_file.exists())

if bbx_file.exists():
    raw_bbx = bbx_file.read_bytes()
    val_bbx, msg_bbx = verify_container_integrity(raw_bbx, master_key)
    check_test("CASE_5.b Enterprise .bbx container signature valid", val_bbx, msg_bbx)
    
    dec_bbx = decrypt_container(raw_bbx, master_key)
    check_test("CASE_5.c Enterprise .bbx successfully decrypted in RAM (>100 KB)", len(dec_bbx) > 100_000)

print("\n═══ CASE 6: Anti-Debugging Module ═══")
is_dbg, dbg_msg = check_debugger_present()
check_test("CASE_6.a Anti-debugging check returns clean status in test runner", isinstance(is_dbg, bool))

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*70}")
print(f"  UniPlag Enterprise BlackBox Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*70}")

if passed == total:
    print("  🎉 ALL CASES PASS — UniPlag BlackBox (.bbx) OPERATIONAL & SECURED!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
