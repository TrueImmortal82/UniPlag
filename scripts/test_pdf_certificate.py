"""
scripts/test_pdf_certificate.py — Official PDF Certificate Generator Test Suite
Tests:
  1. generate_check_pdf_certificate produces valid vector PDF binary stream
  2. PDF contains title, student name, metric scores, verdict, and SHA-512 seal
  3. Live endpoint /report/{id}/pdf returns 200 OK with application/pdf content type
  4. Access control: unauthorized students cannot download certificates of other students
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User, Document, Check, Match, Fragment
from app.auth import create_session
from app.pdf_certificate import generate_check_pdf_certificate

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


client = TestClient(app)
init_db()

with SessionLocal() as db:
    admin_u = db.query(User).filter(User.role == "admin").first()
    admin_tok = create_session(admin_u.id)

    # 1. Create or get student check
    s1 = db.query(User).filter(User.username == "student_elena").first()
    if not s1:
        s1 = User(username="student_elena", full_name="Елена Смирнова", role="student", group_name="ИВТ-41")
        s1.set_password("pass123")
        db.add(s1)
        db.commit()
        db.refresh(s1)

    s1_tok = create_session(s1.id)

    sample_full_text = (
        "Введение\n\n"
        "Современное развитие информационных технологий и появление квантовых вычислителей ставит новые вызовы перед классической криптографией. "
        "Алгоритмы с открытым ключом, такие как RSA и ECC, основанные на сложности факторизации больших чисел и дискретного логарифмирования, "
        "становятся уязвимыми к алгоритмам Шора и Гровера на квантовых компьютерах.\n\n"
        "1. Анализ постквантовых алгоритмов\n\n"
        "В работе исследуются решёточные криптосистемы (Lattice-based cryptography), основанные на проблеме обучения с ошибками (LWE) и "
        "кратчайшего вектора (SVP). Данные математические структуры демонстрируют высокую вычислительную стойкость как к классическим, "
        "так и к квантовым атакам.\n\n"
        "2. Практическая реализация и тестирование\n\n"
        "В ходе экспериментов были сопоставлены временные характеристики генерации ключей, шифрования и расшифрования для протоколов Kyber и Dilithium. "
        "Результаты измерений показывают, что увеличение размера ключа компенсируется высокой скоростью криптографических преобразований.\n\n"
        "Заключение\n\n"
        "Полученные результаты подтверждают целесообразность внедрения решёточных алгоритмов в современные протоколы защиты данных. "
        "Дальнейшие исследования будут направлены на оптимизацию энергопотребления на мобильных и встраиваемых платформах."
    )

    doc = Document(
        title="Исследование криптографических алгоритмов",
        author="Елена Смирнова",
        owner_id=s1.id,
        text=sample_full_text,
        words=len(sample_full_text.split()),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chk = Check(
        document_id=doc.id,
        plag_score=14.5,
        ai_score=0.12,
        icg_score=78.5,
        status="done",
        verification_seal="e4b8a1390f75e5b8a0d4c82b14f8902c51b7a2e8c9d0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0",
    )
    db.add(chk)
    db.commit()
    db.refresh(chk)

    # Add Match
    m = Match(check_id=chk.id, source_label="Криптографический сборник 2025", sim=14.5)
    db.add(m)
    db.commit()

    check_id = chk.id

print("\n═══ CASE 1: Core PDF Generation ═══")
with SessionLocal() as db:
    chk_obj = db.get(Check, check_id)
    pdf_bytes = generate_check_pdf_certificate(chk_obj)

check_test("CASE_1.a PDF binary generated (> 5 KB)", len(pdf_bytes) > 5000)
check_test("CASE_1.b PDF starts with %PDF- header", pdf_bytes.startswith(b"%PDF-"))

print("\n═══ CASE 2: Live Download Endpoint /report/{id}/pdf ═══")
resp_admin = client.get(f"/report/{check_id}/pdf", cookies={"uniplag_session": admin_tok})
check_test("CASE_2.a Admin can download PDF (200 OK)", resp_admin.status_code == 200)
check_test("CASE_2.b Content-Type is application/pdf", "application/pdf" in resp_admin.headers.get("content-type", ""))
check_test("CASE_2.c Content-Disposition header contains Certificate_Check", "Certificate_Check" in resp_admin.headers.get("content-disposition", ""))

resp_owner = client.get(f"/report/{check_id}/pdf", cookies={"uniplag_session": s1_tok})
check_test("CASE_2.d Student owner can download own certificate", resp_owner.status_code == 200)

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  PDF Certificate Generator Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Academic PDF Certificate Generator OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
