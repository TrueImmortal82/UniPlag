"""
scripts/test_text_viewer.py — Scrollable Document Text Viewer Test Suite
Tests:
  1. build_highlighted_html correctly highlights plagiarism and AI spans
  2. build_highlighted_html safely handles None / empty documents
  3. build_highlighted_html safely bounds out-of-range offsets
  4. Live /report/{id} renders the scrollable text window (.doc-text-window)
  5. Live /report/{id} contains zoom controls, copy button, and fullscreen trigger
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app, build_highlighted_html
from app.db import init_db, SessionLocal, User, Document, Check, Match, Fragment
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

print("\n═══ CASE 1: Safe HTML Highlighting with Bounds Protection ═══")
with SessionLocal() as db:
    # 1. Normal document
    d_normal = Document(title="Тест текста", author="Студент", text="Это тестовый текст работы с заимствованием и анализом.")
    db.add(d_normal)
    db.commit()
    db.refresh(d_normal)
    
    c_normal = Check(document_id=d_normal.id, plag_score=20.0, status="done")
    db.add(c_normal)
    db.commit()
    db.refresh(c_normal)

    # Add match
    m = Match(check_id=c_normal.id, source_label="Источник 1", sim=25.0)
    db.add(m)
    db.commit()
    db.refresh(m)
    fr = Fragment(match_id=m.id, q_start=4, q_end=12, text="тестовый")
    db.add(fr)
    db.commit()

    html_out = build_highlighted_html(db, c_normal)
    check_test("CASE_1.a Normal text highlighted with frag-plag", "frag-plag" in html_out)

    # 2. Out of bounds offsets
    fr_oob = Fragment(match_id=m.id, q_start=100, q_end=200, text="выход за границы")
    db.add(fr_oob)
    db.commit()
    html_oob = build_highlighted_html(db, c_normal)
    check_test("CASE_1.b Out-of-bounds offsets handled without crash", len(html_oob) > 0)

    # 3. Empty document
    d_empty = Document(title="Пустой документ", author="Студент", text="")
    db.add(d_empty)
    db.commit()
    db.refresh(d_empty)
    c_empty = Check(document_id=d_empty.id, status="done")
    db.add(c_empty)
    db.commit()
    html_empty = build_highlighted_html(db, c_empty)
    check_test("CASE_1.c Empty document returns safe fallback message", "отсутствует" in html_empty or "пуст" in html_empty)

    check_id = c_normal.id
    u = db.query(User).filter(User.role == "admin").first()
    tok = create_session(u.id)

print("\n═══ CASE 2: Live Report Page Scroll Window & Tools ═══")
r = client.get(f"/report/{check_id}", cookies={"uniplag_session": tok})
check_test("CASE_2.a /report/{id} returns 200 OK", r.status_code == 200)
check_test("CASE_2.b Report contains scroll container '#text-scroll-window'", "text-scroll-window" in r.text)
check_test("CASE_2.c Report contains CSS class 'doc-text-window'", "doc-text-window" in r.text)
check_test("CASE_2.d Report contains font zoom buttons (A- / A+)", "changeFontSize" in r.text)
check_test("CASE_2.e Report contains copy button", "copyDocumentText" in r.text)
check_test("CASE_2.f Report contains fullscreen button", "toggleFullscreenText" in r.text)
check_test("CASE_2.g Report contains word count and char count", "Слов:" in r.text and "Символов:" in r.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Scrollable Text Viewer Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Scrollable Document Text Viewer OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
