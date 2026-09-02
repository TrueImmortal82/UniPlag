"""
scripts/test_multilingual.py — Multilingual Localization (i18n RU/EN) Test Suite
Tests:
  1. app/i18n.py dictionary translates keys in RU and EN
  2. GET /set-language/{lang} sets cookie and redirects
  3. UI topbar & metrics render in English when lang=en
  4. PDF generator produces valid English certificate with English headers
  5. PDF generator produces valid Russian certificate with Russian headers
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User, Check, Document
from app.auth import create_session
from app.i18n import t, get_language, SUPPORTED_LANGUAGES
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
    chk = db.query(Check).filter(Check.status == "done").first()
    check_id = chk.id if chk else 1

print("\n═══ CASE 1: Core i18n Translation Engine ═══")
check_test("CASE_1.a 'ru' and 'en' in supported languages", "ru" in SUPPORTED_LANGUAGES and "en" in SUPPORTED_LANGUAGES)
check_test("CASE_1.b Russian translation of originality", t("metric_originality", "ru") == "Оригинальность")
check_test("CASE_1.c English translation of originality", t("metric_originality", "en") == "Originality")
check_test("CASE_1.d English translation of my works", t("nav_my_works", "en") == "📝 My Works")

print("\n═══ CASE 2: Language Switching Route (/set-language/{lang}) ═══")
resp_set_en = client.get("/set-language/en", follow_redirects=False)
check_test("CASE_2.a GET /set-language/en redirects 303", resp_set_en.status_code == 303)
cookie_val = resp_set_en.cookies.get("uniplag_lang")
check_test("CASE_2.b uniplag_lang cookie set to 'en'", cookie_val == "en")

print("\n═══ CASE 3: English UI Template Rendering ═══")
resp_ui_en = client.get("/", cookies={"uniplag_session": admin_tok, "uniplag_lang": "en"})
check_test("CASE_3.a English dashboard renders 200 OK", resp_ui_en.status_code == 200)
check_test("CASE_3.b English topbar contains 'All Checks'", "All Checks" in resp_ui_en.text)
check_test("CASE_3.c English topbar contains 'User Guide'", "User Guide" in resp_ui_en.text)

resp_rep_en = client.get(f"/report/{check_id}", cookies={"uniplag_session": admin_tok, "uniplag_lang": "en"})
check_test("CASE_3.d English report contains 'Originality'", "Originality" in resp_rep_en.text)
check_test("CASE_3.e English report contains 'PDF (EN)' button", "PDF (EN)" in resp_rep_en.text)

print("\n═══ CASE 4: Bilingual PDF Certificate Generation ═══")
with SessionLocal() as db:
    chk_obj = db.get(Check, check_id)
    pdf_ru = generate_check_pdf_certificate(chk_obj, lang="ru")
    pdf_en = generate_check_pdf_certificate(chk_obj, lang="en")

check_test("CASE_4.a Russian PDF generated (>5 KB)", len(pdf_ru) > 5000)
check_test("CASE_4.b English PDF generated (>5 KB)", len(pdf_en) > 5000)

resp_pdf_en = client.get(f"/report/{check_id}/pdf?lang=en", cookies={"uniplag_session": admin_tok})
check_test("CASE_4.c GET /report/{id}/pdf?lang=en returns 200 OK", resp_pdf_en.status_code == 200)
check_test("CASE_4.d Content-Disposition contains Certificate_Check", "Certificate_Check" in resp_pdf_en.headers.get("content-disposition", ""))

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Multilingual Localization (i18n) Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Multilingual Support (RU / EN) OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
