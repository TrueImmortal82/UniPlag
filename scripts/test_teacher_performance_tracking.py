"""
scripts/test_teacher_performance_tracking.py — Teacher Student Performance Tracking & Risk Analysis Test Suite
Tests:
  1. Classification of performing students (High ICG, High Orig, Low AI)
  2. Classification of struggling/at-risk students (Low ICG, High AI, High Plag, or 0 works)
  3. Risk reason diagnosis generation
  4. Teacher student assignment (teacher_id)
  5. Teacher dashboard filtering (my_students, performing, at_risk)
  6. Visual status indicators and performance stat counters
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app, compute_student_ratings
from app.db import init_db, SessionLocal, User, Document, Check
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
    # 1. Create a Teacher
    prof = db.query(User).filter(User.username == "prof_voronov").first()
    if not prof:
        prof = User(username="prof_voronov", full_name="проф. Воронов К.М.", role="teacher")
        prof.set_password("prof123")
        db.add(prof)
        db.commit()
        db.refresh(prof)
    teacher_id = prof.id
    prof_token = create_session(prof.id)

    # 2. Student 1: Top performer assigned to prof_voronov
    s_top = db.query(User).filter(User.username == "student_elena").first()
    if not s_top:
        s_top = User(username="student_elena", full_name="Елена Васильева", role="student", group_name="ИВТ-41", teacher_id=teacher_id)
        s_top.set_password("pass123")
        db.add(s_top)
        db.commit()
        db.refresh(s_top)
    else:
        s_top.teacher_id = teacher_id
        db.commit()

    sample_full_text = (
        "Введение и постановка задачи\n\n"
        "Исследование посвящено анализу современных методов синтеза семантических сетей и реферативной криптографии. "
        "В ходе работы проведён сопоставительный анализ точности моделей на русскоязычном корпусе академических публикаций.\n\n"
        "Методология и экспериментальные результаты\n\n"
        "Разработанный алгоритм позволяет строить ориентированный граф аргументации с выделением опорных тезисов и авторских выводов."
    )

    d_top = Document(title="Синтез семантических сетей", author="Васильева Е.", owner_id=s_top.id, text=sample_full_text, words=len(sample_full_text.split()))
    db.add(d_top)
    db.commit()
    db.refresh(d_top)
    c_top = Check(document_id=d_top.id, plag_score=10.0, ai_score=0.05, icg_score=75.0, status="done")
    db.add(c_top)

    # 3. Student 2: At-Risk student (Low ICG & high plagiarism) assigned to prof_voronov
    s_risk = db.query(User).filter(User.username == "student_dmitry").first()
    if not s_risk:
        s_risk = User(username="student_dmitry", full_name="Дмитрий Козлов", role="student", group_name="ИВТ-41", teacher_id=teacher_id)
        s_risk.set_password("pass123")
        db.add(s_risk)
        db.commit()
        db.refresh(s_risk)
    else:
        s_risk.teacher_id = teacher_id
        db.commit()

    d_risk = Document(title="Реферат по криптографии", author="Козлов Д.", owner_id=s_risk.id, text=sample_full_text, words=len(sample_full_text.split()))
    db.add(d_risk)
    db.commit()
    db.refresh(d_risk)
    c_risk = Check(document_id=d_risk.id, plag_score=65.0, ai_score=0.70, icg_score=15.0, status="done")
    db.add(c_risk)

    # 4. Student 3: Zero works student
    s_zero = db.query(User).filter(User.username == "student_zero").first()
    if not s_zero:
        s_zero = User(username="student_zero", full_name="Олег Новиков", role="student", group_name="ПИ-32")
        s_zero.set_password("pass123")
        db.add(s_zero)
        db.commit()

    db.commit()

print("\n═══ CASE 1: Diagnostic Performance Classification ═══")
with SessionLocal() as db:
    ratings, groups, counts = compute_student_ratings(db, current_teacher_id=teacher_id)

elena = next((r for r in ratings if r["username"] == "student_elena"), None)
dmitry = next((r for r in ratings if r["username"] == "student_dmitry"), None)
oleg = next((r for r in ratings if r["username"] == "student_zero"), None)

check_test("CASE_1.a Elena is classified as 'performing' (🟢)", elena is not None and elena["performance_status"] == "performing")
check_test("CASE_1.b Elena has badge class 'ok'", elena is not None and elena["status_badge_class"] == "ok")
check_test("CASE_1.c Dmitry is classified as 'at_risk' (🔴)", dmitry is not None and dmitry["performance_status"] == "at_risk")
check_test("CASE_1.d Dmitry's risk reasons identify low ICG & plag/AI", dmitry is not None and any("ICG" in r or "плагиат" in r or "ИИ" in r for r in dmitry["risk_reasons"]))
check_test("CASE_1.e Oleg (0 works) is classified as 'at_risk'", oleg is not None and oleg["performance_status"] == "at_risk")
check_test("CASE_1.f Oleg has '0 сданных работ' risk reason", oleg is not None and "0 сданных работ" in oleg["risk_reasons"][0])


print("\n═══ CASE 2: Teacher Assignment & Counters ═══")
check_test("CASE_2.a Elena is marked as is_assigned for Prof Voronov", elena is not None and elena["is_assigned"] is True)
check_test("CASE_2.b Dmitry is marked as is_assigned for Prof Voronov", dmitry is not None and dmitry["is_assigned"] is True)
check_test("CASE_2.c Oleg is not assigned to Prof Voronov", oleg is not None and oleg["is_assigned"] is False)
check_test("CASE_2.d Performing counter >= 1", counts["performing"] >= 1)
check_test("CASE_2.e At-risk counter >= 2", counts["at_risk"] >= 2)
check_test("CASE_2.f My students counter >= 2", counts["my_students"] >= 2)


print("\n═══ CASE 3: Status Filtering ═══")
with SessionLocal() as db:
    ratings_perf, _, _ = compute_student_ratings(db, status_filter="performing", current_teacher_id=teacher_id)
    ratings_risk, _, _ = compute_student_ratings(db, status_filter="at_risk", current_teacher_id=teacher_id)
    ratings_my, _, _ = compute_student_ratings(db, status_filter="my_students", current_teacher_id=teacher_id)

check_test("CASE_3.a status=performing returns only performing students", all(r["performance_status"] == "performing" for r in ratings_perf))
check_test("CASE_3.b status=at_risk returns only at_risk students", all(r["performance_status"] == "at_risk" for r in ratings_risk))
check_test("CASE_3.c status=my_students returns only Voronov's students", all(r["is_assigned"] is True for r in ratings_my))


print("\n═══ CASE 4: Live Teacher Dashboard UI (/ & /?status=...) ═══")
r_dash = client.get("/", cookies={"uniplag_session": prof_token})
check_test("CASE_4.a Teacher dashboard returns 200 OK", r_dash.status_code == 200)
check_test("CASE_4.b Dashboard displays 'Успевающие (Высокий ICG)' counter", "Успевающие (Высокий ICG)" in r_dash.text)
check_test("CASE_4.c Dashboard displays 'В зоне риска / Не успевают' counter", "В зоне риска" in r_dash.text)
check_test("CASE_4.d Dashboard renders 'Ваш студент' badge for assigned students", "Ваш студент" in r_dash.text)
check_test("CASE_4.e Dashboard displays Elena as performing", "student_elena" in r_dash.text and "Успевает" in r_dash.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Teacher Student Performance Tracking Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Teacher Performance Tracking & Risk Analysis OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
