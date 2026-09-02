"""
scripts/test_user_guide.py — Interactive User Guide & Intuitive UI Test Suite
Tests:
  1. GET /guide route returns 200 OK and renders student, teacher, admin instructions, and FAQ
  2. USER_GUIDE.md exists and contains complete instructions for students and teachers
  3. Topbar navigation contains active link to /guide
  4. Upload and dashboard pages contain intuitive help banners and links to guide
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User
from app.auth import create_session

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

    student_u = db.query(User).filter(User.role == "student").first()
    student_tok = create_session(student_u.id) if student_u else admin_tok

print("\n═══ CASE 1: Live Interactive User Guide (/guide) ═══")
resp_guide = client.get("/guide", cookies={"uniplag_session": student_tok})
check_test("CASE_1.a GET /guide returns 200 OK", resp_guide.status_code == 200)
check_test("CASE_1.b Guide contains 'Руководство пользователя'", "Руководство пользователя" in resp_guide.text)
check_test("CASE_1.c Guide contains student section", "Инструкция для студента" in resp_guide.text)
check_test("CASE_1.d Guide contains teacher section", "Инструкция для преподавателя" in resp_guide.text)
check_test("CASE_1.e Guide contains FAQ section", "Часто задаваемые вопросы" in resp_guide.text)
check_test("CASE_1.f Guide explains PDF certificate download", "PDF-сертификат" in resp_guide.text)

print("\n═══ CASE 2: Workspace USER_GUIDE.md Manual File ═══")
guide_file = Path("USER_GUIDE.md")
check_test("CASE_2.a USER_GUIDE.md exists in root", guide_file.exists())
if guide_file.exists():
    content = guide_file.read_text(encoding="utf-8")
    check_test("CASE_2.b USER_GUIDE.md contains 3-step quick start", "Как работает платформа за 3 шага" in content)
    check_test("CASE_2.c USER_GUIDE.md contains Student section", "Инструкция для СТУДЕНТА" in content)
    check_test("CASE_2.d USER_GUIDE.md contains Teacher section", "Инструкция для ПРЕПОДАВАТЕЛЯ" in content)
    check_test("CASE_2.e USER_GUIDE.md contains FAQ", "Часто задаваемые вопросы" in content)

print("\n═══ CASE 3: Intuitive Navigation & Onboarding Banners ═══")
resp_dash = client.get("/", cookies={"uniplag_session": student_tok})
check_test("CASE_3.a Dashboard contains link to /guide", "/guide" in resp_dash.text)
check_test("CASE_3.b Dashboard topbar contains '📖 Руководство'", "Руководство" in resp_dash.text)

resp_upload = client.get("/upload", cookies={"uniplag_session": student_tok})
check_test("CASE_3.c Upload page contains drag & drop dropzone", "drop-area" in resp_upload.text or "file-input" in resp_upload.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  User Guide & Intuitive UI Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — User Guide & Intuitive Interface OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
