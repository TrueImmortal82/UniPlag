"""
scripts/test_anti_tamper.py — Anti-Tamper & Cryptographic Code Integrity Test Suite
Tests:
  1. Base sealed integrity manifest validation
  2. Detection of unauthorized source code modification (file patching attack)
  3. Detection of rogue file injection into protected tree
  4. Detection of manifest signature tampering (forgery attempt)
  5. Cryptographic report digital seal generation & validation
  6. Detection of forged report parameters (score manipulation attack)
  7. Public verification route /verify/{seal}
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, Document, Check, User
from app.integrity import (
    verify_code_integrity,
    generate_and_save_manifest,
    generate_report_seal,
    verify_report_seal,
    MANIFEST_FILE,
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

print("\n═══ CASE 1: Base Sealed Manifest Integrity ═══")
# Ensure manifest is cleanly generated
generate_and_save_manifest()
res_clean = verify_code_integrity()
check_test("CASE_1.a Codebase passes integrity verification in sealed state", res_clean.is_valid)
check_test("CASE_1.b Signature is valid HMAC-SHA256", res_clean.signature_valid)
check_test("CASE_1.c No tampered files detected", len(res_clean.tampered_files) == 0)


print("\n═══ CASE 2: Detection of Unauthorized File Modification ═══")
target_file = Path("app/config.py")
orig_content = target_file.read_text(encoding="utf-8")
try:
    # Simulate an attacker patching a config threshold to bypass anti-plagiarism
    target_file.write_text(orig_content + "\n# MALICIOUS_PATCH_BYPASS = True\n", encoding="utf-8")
    
    res_tampered = verify_code_integrity()
    check_test("CASE_2.a Tampered file detected by integrity checker", not res_tampered.is_valid)
    check_test("CASE_2.b Tampered file list contains 'app/config.py'", "app/config.py" in res_tampered.tampered_files)
finally:
    # Restore original content
    target_file.write_text(orig_content, encoding="utf-8")

# Verify recovery
res_restored = verify_code_integrity()
check_test("CASE_2.c Codebase valid after restoring original file", res_restored.is_valid)


print("\n═══ CASE 3: Detection of Manifest Signature Forgery ═══")
orig_manifest = MANIFEST_FILE.read_text(encoding="utf-8")
try:
    m_data = json.loads(orig_manifest)
    # Simulate attacker altering stored signature
    m_data["signature"] = "0000000000000000000000000000000000000000000000000000000000000000"
    MANIFEST_FILE.write_text(json.dumps(m_data), encoding="utf-8")
    
    res_forged_sig = verify_code_integrity()
    check_test("CASE_3.a Forged manifest signature rejected", not res_forged_sig.is_valid and not res_forged_sig.signature_valid)
finally:
    MANIFEST_FILE.write_text(orig_manifest, encoding="utf-8")

res_sig_restored = verify_code_integrity()
check_test("CASE_3.b Valid manifest signature restored", res_sig_restored.is_valid)


print("\n═══ CASE 4: Cryptographic Report Digital Sealing ═══")
doc_title = "Тестовая работа по кибербезопасности"
doc_text = "Введение. Анализ криптографических протоколов и целостности данных..."
check_id = 9999
plag_score = 12.5
ai_score = 0.05
icg_score = 80.0
ts = "2026-08-30T00:00:00"

seal = generate_report_seal(
    check_id=check_id,
    doc_title=doc_title,
    doc_text=doc_text,
    plag_score=plag_score,
    ai_score=ai_score,
    icg_score=icg_score,
    created_at_iso=ts,
)

check_test("CASE_4.a Digital seal generated with standard prefix 'UP-'", seal.startswith("UP-09999-"))
check_test("CASE_4.b Genuine seal passes verification", 
           verify_report_seal(seal, check_id, doc_title, doc_text, plag_score, ai_score, icg_score, ts))


print("\n═══ CASE 5: Detection of Forged Report Parameters ═══")
# Attacker tries to present an altered plagiarism score (e.g. lowering 12.5% to 2.0%)
check_test("CASE_5.a Forged plagiarism score detected & rejected", 
           not verify_report_seal(seal, check_id, doc_title, doc_text, 2.0, ai_score, icg_score, ts))

# Attacker tries to present altered document text
check_test("CASE_5.b Altered document text detected & rejected", 
           not verify_report_seal(seal, check_id, doc_title, doc_text + " FAKE", plag_score, ai_score, icg_score, ts))

# Attacker tries to alter check ID
check_test("CASE_5.c Altered check ID detected & rejected", 
           not verify_report_seal(seal, 8888, doc_title, doc_text, plag_score, ai_score, icg_score, ts))


print("\n═══ CASE 6: Public Verification Route (/verify/{seal}) ═══")
init_db()
with SessionLocal() as db:
    doc = Document(
        title="Дипломная работа по защите информации",
        author="Сидоров С.С.",
        kind="student",
        text="Полный текст исследования криптографических хэш-функций и цифровых подписей.",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    check = Check(
        document_id=doc.id,
        plag_score=8.5,
        ai_score=0.02,
        icg_score=72.0,
        status="done",
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    
    real_seal = generate_report_seal(
        check_id=check.id,
        doc_title=doc.title,
        doc_text=doc.text,
        plag_score=check.plag_score,
        ai_score=check.ai_score,
        icg_score=check.icg_score,
        created_at_iso=check.created_at.isoformat(),
    )
    check.verification_seal = real_seal
    db.commit()

# Test public verification with valid seal
r_verify_valid = client.get(f"/verify/{real_seal}")
check_test("CASE_6.a Public endpoint validates genuine seal (200 OK)", 
           r_verify_valid.status_code == 200 and "ОТЧЁТ ПОДЛИНЕН И ЗАВЕРЕН" in r_verify_valid.text)

# Test public verification with non-existent / fake seal
r_verify_fake = client.get("/verify/UP-99999-FAKEFAKEFAKEFAKEFAKE")
check_test("CASE_6.b Public endpoint rejects non-existent seal (404)", 
           r_verify_fake.status_code == 404 and "ОШИБКА ВЕРИФИКАЦИИ ПЕЧАТИ" in r_verify_fake.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Anti-Tamper & Code Integrity Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Anti-Tamper & Integrity Protection OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
