"""
scripts/test_icg_recommendations.py — ICG Pedagogical Recommendation Engine Test Suite
Tests:
  1. Low synthesis profile generates literature synthesis advice
  2. High unsupported ratio generates evidence anchoring advice
  3. Contradictory profile generates logical consistency advice
  4. High quality profile recognizes strengths and provides checklist
  5. Live report page (/report/{id}) includes personalized ICG recommendations block
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User, Document, Check
from app.auth import create_session
from app.icg.recommendations import generate_icg_recommendations

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


print("\n═══ CASE 1: Low Synthesis Profile (Reproduction dominant) ═══")
rec_low_synth = generate_icg_recommendations(
    icg_data={
        "ratios": {"synthesis": 0.05, "inference": 0.08, "reproduction": 0.85, "unsupported": 0.02},
        "summary": {"intellectual_contribution_score": 0.18}
    },
    plag_score=15.0,
    ai_score=0.05,
    icg_score=18.0
)

check_test("CASE_1.a Low synthesis verdict is bad/warning", rec_low_synth["verdict_class"] in ("bad", "warn"))
check_test("CASE_1.b Top priority mentions synthesis/реферативность", "синтез" in rec_low_synth["top_priority"].lower() or "реферативност" in rec_low_synth["top_priority"].lower())
check_test("CASE_1.c Growth area contains literature synthesis advice", any("синтез" in g["title"].lower() for g in rec_low_synth["growth_areas"]))
check_test("CASE_1.d Checklist contains action step", len(rec_low_synth["action_checklist"]) >= 1)


print("\n═══ CASE 2: High Unsupported Claims Profile ═══")
rec_unsupp = generate_icg_recommendations(
    icg_data={
        "ratios": {"synthesis": 0.20, "inference": 0.15, "reproduction": 0.35, "unsupported": 0.30},
        "summary": {"intellectual_contribution_score": 0.35}
    },
    plag_score=10.0,
    ai_score=0.10,
    icg_score=35.0
)

check_test("CASE_2.a Top priority identifies unsupported assertions", "ссылк" in rec_unsupp["top_priority"].lower() or "бездоказательн" in rec_unsupp["top_priority"].lower() or "доказательн" in rec_unsupp["top_priority"].lower())
check_test("CASE_2.b Growth area flags citation discipline", any("доказательн" in g["title"].lower() or "цитирован" in g["title"].lower() for g in rec_unsupp["growth_areas"]))


print("\n═══ CASE 3: Logical Contradictions Profile ═══")
rec_contra = generate_icg_recommendations(
    icg_data={
        "ratios": {"synthesis": 0.25, "inference": 0.20, "contradictory": 0.12},
        "summary": {"intellectual_contribution_score": 0.40}
    },
    plag_score=12.0,
    ai_score=0.05,
    icg_score=40.0
)

check_test("CASE_3.a Top priority flags logical contradictions", "противореч" in rec_contra["top_priority"].lower())
check_test("CASE_3.b Critical tag applied to contradiction growth area", any(g["tag_class"] == "bad" for g in rec_contra["growth_areas"]))


print("\n═══ CASE 4: High Intellectual Contribution Profile ═══")
rec_high = generate_icg_recommendations(
    icg_data={
        "ratios": {"synthesis": 0.40, "inference": 0.35, "reproduction": 0.25, "unsupported": 0.0},
        "summary": {"intellectual_contribution_score": 0.85}
    },
    plag_score=8.0,
    ai_score=0.02,
    icg_score=85.0
)

check_test("CASE_4.a High ICG verdict is 'ok'", rec_high["verdict_class"] == "ok")
check_test("CASE_4.b Multiple strengths identified (>=2)", len(rec_high["strengths"]) >= 2)
check_test("CASE_4.c Academic phrasing templates included (>=3)", len(rec_high["phrasing_templates"]) >= 3)


print("\n═══ CASE 5: Live Report Page Rendering (/report/{id}) ═══")
client = TestClient(app)
init_db()

with SessionLocal() as db:
    s = db.query(User).filter(User.username == "student_ivan").first()
    tok = create_session(s.id)
    doc = db.query(Document).filter(Document.owner_id == s.id).first()
    chk = db.query(Check).filter(Check.document_id == doc.id).first()
    chk_id = chk.id

r_rep = client.get(f"/report/{chk_id}", cookies={"uniplag_session": tok})
check_test("CASE_5.a Report page returns 200 OK", r_rep.status_code == 200)
check_test("CASE_5.b Report contains 'Персональные ICG-рекомендации'", "Персональные ICG-рекомендации" in r_rep.text)
check_test("CASE_5.c Report contains 'Академический вердикт'", "Академический вердикт" in r_rep.text)
check_test("CASE_5.d Report contains 'Пошаговый чек-лист'", "Пошаговый чек-лист" in r_rep.text)
check_test("CASE_5.e Report contains 'Готовые шаблоны академических формулировок'", "Готовые шаблоны академических формулировок" in r_rep.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  ICG Recommendations Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Student ICG Pedagogical Recommendations OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
