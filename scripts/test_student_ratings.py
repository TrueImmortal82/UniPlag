"""
scripts/test_student_ratings.py — Student Aggregation & ICG Title Test Suite
Tests:
  1. compute_student_ratings groups works by student_id
  2. Average originality, AI %, and ICG score calculation
  3. Ranking assignment based on composite academic score
  4. Group filtering for student ratings
  5. /admin/icg includes document title, author, and student_id
  6. Dashboard renders student rating leaderboard
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
    # Setup test students
    s1 = db.query(User).filter(User.username == "student_ivan").first()
    if not s1:
        s1 = User(username="student_ivan", full_name="Иванов Иван", role="student", group_name="ИВТ-41")
        s1.set_password("pass123")
        db.add(s1)
        db.commit()
        db.refresh(s1)

    s2 = db.query(User).filter(User.username == "student_anna").first()
    if not s2:
        s2 = User(username="student_anna", full_name="Анна Смирнова", role="student", group_name="ПИ-32")
        s2.set_password("pass123")
        db.add(s2)
        db.commit()
        db.refresh(s2)

    sample_full_text = (
        "Введение и актуальность\n\n"
        "Исследование посвящено анализу современных методов построения графов рассуждений и семантической связности текстов. "
        "В ходе работы проведён сопоставительный анализ точности NLI-моделей на русскоязычном корпусе академических публикаций.\n\n"
        "Методология и результаты\n\n"
        "Разработанный алгоритм позволяет строить ориентированный ациклический граф аргументации с выделением опорных тезисов и выводов автора."
    )

    # Add works for s1 (Ivan: 2 works, high orig, high ICG)
    d1 = Document(title="Исследование графов рассуждений", author="Иванов И.", owner_id=s1.id, text=sample_full_text, words=len(sample_full_text.split()))
    d2 = Document(title="Сравнительный анализ NLI-моделей", author="Иванов И.", owner_id=s1.id, text=sample_full_text, words=len(sample_full_text.split()))
    db.add_all([d1, d2])
    db.commit()
    db.refresh(d1)
    db.refresh(d2)

    c1 = Check(document_id=d1.id, plag_score=10.0, ai_score=0.05, icg_score=80.0, status="done")
    c2 = Check(document_id=d2.id, plag_score=20.0, ai_score=0.10, icg_score=70.0, status="done")
    db.add_all([c1, c2])

    # Add works for s2 (Anna: 1 work, medium orig)
    d3 = Document(title="Разработка веб-сервиса на FastAPI", author="Смирнова А.", owner_id=s2.id, text=sample_full_text, words=len(sample_full_text.split()))
    db.add(d3)
    db.commit()
    db.refresh(d3)
    c3 = Check(document_id=d3.id, plag_score=35.0, ai_score=0.30, icg_score=45.0, status="done")
    db.add(c3)
    db.commit()

    admin_u = db.query(User).filter(User.role == "admin").first()
    admin_tok = create_session(admin_u.id)

print("\n═══ CASE 1: Student Rating Computation & Aggregation ═══")
with SessionLocal() as db:
    ratings, groups, _ = compute_student_ratings(db)

check_test("CASE_1.a Student ratings computed", len(ratings) >= 2)
ivan_r = next((r for r in ratings if r["username"] == "student_ivan"), None)
check_test("CASE_1.b Ivan's works count is 2", ivan_r is not None and ivan_r["works_count"] >= 2)

# Ivan: plag=(10+20)/2=15 -> orig=85, icg=(80+70)/2=75, ai=7.5%
check_test("CASE_1.c Ivan's avg originality is 85.0%", ivan_r is not None and abs(ivan_r["avg_orig"] - 85.0) < 0.2)
check_test("CASE_1.d Ivan's avg ICG score is 75.0%", ivan_r is not None and abs(ivan_r["avg_icg"] - 75.0) < 0.2)
check_test("CASE_1.e Groups list contains 'ИВТ-41' and 'ПИ-32'", "ИВТ-41" in groups and "ПИ-32" in groups)


print("\n═══ CASE 2: Ranking & Tier Classification ═══")
check_test("CASE_2.a Students are ranked in descending order", ratings[0]["rating_score"] >= ratings[1]["rating_score"])
check_test("CASE_2.b Ivan has tier 'Лидер (Высший вклад)'", ivan_r is not None and "Лидер" in ivan_r["tier"])


print("\n═══ CASE 3: Group Filtering ═══")
with SessionLocal() as db:
    ratings_ivt, _, _ = compute_student_ratings(db, group_filter="ИВТ-41")
check_test("CASE_3.a Filter by 'ИВТ-41' returns only ИВТ-41 students", all(r["group_name"] == "ИВТ-41" for r in ratings_ivt))


print("\n═══ CASE 4: /admin/icg Displays Work Titles & Student IDs ═══")
r_icg = client.get("/admin/icg", cookies={"uniplag_session": admin_tok})
check_test("CASE_4.a /admin/icg returns 200 OK", r_icg.status_code == 200)
check_test("CASE_4.b /admin/icg contains document title 'Исследование графов рассуждений'", "Исследование графов рассуждений" in r_icg.text)
check_test("CASE_4.c /admin/icg displays Student ID badge", "Student ID" in r_icg.text or "ID:" in r_icg.text)


print("\n═══ CASE 5: Dashboard Leaderboard Rendering ═══")
r_dash = client.get("/?tab=students", cookies={"uniplag_session": admin_tok})
check_test("CASE_5.a Teacher dashboard displays 'Рейтинг студентов'", "Рейтинг студентов" in r_dash.text or "Академический рейтинг" in r_dash.text)
check_test("CASE_5.b Teacher dashboard displays student name 'Иванов Иван'", "Иванов Иван" in r_dash.text)
check_test("CASE_5.c Teacher dashboard displays rank medal 🥇", "🥇" in r_dash.text or "#1" in r_dash.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Student Ratings & ICG Titles Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Student Ratings & ICG Work Titles OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
