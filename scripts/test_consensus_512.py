"""
scripts/test_consensus_512.py — 512-bit Cryptography & Change Consensus Automated Test Suite
Tests:
  1. 512-bit Sovereign Key entropy, bit length (512 bits), and .gitignore isolation
  2. HMAC-SHA512 Manifest signature computation
  3. Pending change delta inspection (modified, added, removed files)
  4. Change approval & Chained Audit Ledger block creation
  5. Cryptographic audit ledger verification (tamper-detection in blockchain history)
  6. Admin change consensus UI & API route security gates (RBAC)
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User
from app.auth import create_session
from app.integrity import (
    get_sovereign_key_512,
    get_sovereign_key_info,
    verify_code_integrity,
    SOVEREIGN_KEY_FILE,
)
from app.consensus import (
    inspect_pending_changes,
    approve_and_seal_changes,
    read_audit_ledger,
    verify_audit_ledger,
    LEDGER_FILE,
)

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


client = TestClient(app)

print("\n═══ CASE 1: 512-bit Key Entropy & Git Isolation ═══")
key_bytes = get_sovereign_key_512()
key_info = get_sovereign_key_info()

check_test("CASE_1.a Sovereign Key bit length is exactly 512 bits (64 bytes)", len(key_bytes) == 64 and key_info["key_size_bits"] == 512)
check_test("CASE_1.b Algorithm configured as HMAC-SHA512", key_info["algorithm"] == "HMAC-SHA512")
check_test("CASE_1.c Key file exists locally in .security/sovereign_512.key", SOVEREIGN_KEY_FILE.exists())

# Check .gitignore contents
gitignore_path = Path(".gitignore")
check_test("CASE_1.d .gitignore file exists", gitignore_path.exists())
if gitignore_path.exists():
    gi_content = gitignore_path.read_text(encoding="utf-8")
    check_test("CASE_1.e .security/*.key is strictly excluded in .gitignore", ".security/*.key" in gi_content or "*.key" in gi_content)


print("\n═══ CASE 2: HMAC-SHA512 Manifest Sealing ═══")
block1 = approve_and_seal_changes(author="Vlad & Aris", description="Initial 512-bit Sealed Baseline")
res_integrity = verify_code_integrity()

check_test("CASE_2.a Code integrity valid under 512-bit key", res_integrity.is_valid)
check_test("CASE_2.b Signature is valid HMAC-SHA512", res_integrity.signature_valid)
check_test("CASE_2.c Manifest file contains 512-bit signature (128 hex characters)", len(block1.manifest_signature) == 128)


print("\n═══ CASE 3: Pending Change Delta Inspection ═══")
test_scratch = Path("app/temp_test_delta.py")
try:
    test_scratch.write_text("# Temp delta test\n", encoding="utf-8")
    delta = inspect_pending_changes()
    
    check_test("CASE_3.a Delta inspector detected unapproved change", delta.has_changes)
    check_test("CASE_3.b Added file identified in delta", "app/temp_test_delta.py" in delta.added_files)
finally:
    if test_scratch.exists():
        test_scratch.unlink()

delta_clean = inspect_pending_changes()
check_test("CASE_3.c Delta is clean after file cleanup", not delta_clean.has_changes)


print("\n═══ CASE 4: Cryptographic Chained Audit Ledger ═══")
block2 = approve_and_seal_changes(author="Vlad", description="Test Change Approval Block #2")
blocks = read_audit_ledger()

check_test("CASE_4.a Audit ledger has recorded blocks (>=2)", len(blocks) >= 2)
check_test("CASE_4.b Block index sequence is continuous", blocks[-1].block_index == len(blocks))
check_test("CASE_4.c Block #2 references Block #1 hash as prev_block_hash", blocks[-1].prev_block_hash == blocks[-2].block_hash)
check_test("CASE_4.d Block hash is computed with SHA-512 (128 hex chars)", len(blocks[-1].block_hash) == 128)

ledger_valid, ledger_msg = verify_audit_ledger()
check_test("CASE_4.e Full audit ledger chain cryptographically valid", ledger_valid)


print("\n═══ CASE 5: Detection of Tampered Audit Ledger History ═══")
orig_ledger = LEDGER_FILE.read_text(encoding="utf-8")
try:
    lines = orig_ledger.splitlines()
    if lines:
        tampered_first = json.loads(lines[0])
        # Attacker tries to alter author of block #1
        tampered_first["author"] = "ATTACKER_FORGER"
        lines[0] = json.dumps(tampered_first)
        LEDGER_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        
        tampered_valid, tampered_msg = verify_audit_ledger()
        check_test("CASE_5.a Tampered audit ledger history detected & rejected", not tampered_valid)
finally:
    LEDGER_FILE.write_text(orig_ledger, encoding="utf-8")

restored_valid, _ = verify_audit_ledger()
check_test("CASE_5.b Audit ledger integrity restored", restored_valid)


print("\n═══ CASE 6: Admin Change Consensus Route Protection (RBAC) ═══")
init_db()
with SessionLocal() as db:
    admin_u = db.query(User).filter(User.role == "admin").first()
    teacher_u = db.query(User).filter(User.role == "teacher").first()
    student_u = db.query(User).filter(User.role == "student").first()
    
    admin_tok = create_session(admin_u.id)
    teacher_tok = create_session(teacher_u.id)
    student_tok = create_session(student_u.id)

# Admin can view consensus page
r_consensus_admin = client.get("/admin/consensus", cookies={"uniplag_session": admin_tok})
check_test("CASE_6.a Admin can access /admin/consensus (200 OK)", r_consensus_admin.status_code == 200 and "512-bit Согласование" in r_consensus_admin.text)

# Teacher blocked
r_consensus_teacher = client.get("/admin/consensus", cookies={"uniplag_session": teacher_tok})
check_test("CASE_6.b Teacher blocked from /admin/consensus (403 Forbidden)", r_consensus_teacher.status_code == 403)

# Student blocked
r_consensus_student = client.get("/admin/consensus", cookies={"uniplag_session": student_tok})
check_test("CASE_6.c Student blocked from /admin/consensus (403 Forbidden)", r_consensus_student.status_code == 403)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  512-bit Crypto & Consensus Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — 512-bit Sovereign Encryption & Consensus OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
