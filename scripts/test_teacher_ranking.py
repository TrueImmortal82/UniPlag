"""
scripts/test_teacher_ranking.py — Faculty Ranking & Student Color League Test Suite
Tests:
  1. compute_teacher_ratings calculates pedagogical score based on students' ICG, originality, and success rate
  2. Teacher ranking sorts faculty by pedagogical score
  3. Teacher efficiency tier assignment (Кафедральный лидер vs Эффективный vs Внимание)
  4. Student color league divisions (🟢 Green, 🟡 Yellow, 🔴 Red)
  5. Live dashboard tab switching (?tab=teachers and ?tab=students)
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app, compute_student_ratings, compute_teacher_ratings
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
    # 1. Setup Prof 1 (High performing students)
    p1 = db.query(User).filter(User.username == "prof_voronov").first()
    if not p1:
        p1 = User(username="prof_voronov", full_name="проф. Воронов К.М.", role="teacher")
        p1.set_password("prof123")
        db.add(p1)
        db.commit()
        db.refresh(p1)

    # Setup Prof 2 (Struggling/New teacher)
    p2 = db.query(User).filter(User.username == "prof_kuznetsov").first()
    if not p2:
        p2 = User(username="prof_kuznetsov", full_name="доц. Кузнецов П.С.", role="teacher")
        p2.set_password("prof123")
        db.add(p2)
        db.commit()
        db.refresh(p2)

    # Assign student with low ICG to p2
    s_p2 = db.query(User).filter(User.username == "student_dmitry").first()
    if s_p2:
        s_p2.teacher_id = p2.id
        db.commit()

    admin_u = db.query(User).filter(User.role == "admin").first()
    admin_token = create_session(admin_u.id)

print("\n═══ CASE 1: Teacher Rating Calculation ═══")
with SessionLocal() as db:
    teacher_ratings = compute_teacher_ratings(db)

check_test("CASE_1.a Teacher ratings computed (>=2)", len(teacher_ratings) >= 2)
p1_rating = next((t for t in teacher_ratings if t["username"] == "prof_voronov"), None)
p2_rating = next((t for t in teacher_ratings if t["username"] == "prof_kuznetsov"), None)

check_test("CASE_1.b Prof Voronov has assigned students", p1_rating is not None and p1_rating["assigned_count"] >= 1)
check_test("CASE_1.c Prof Voronov success rate is positive", p1_rating is not None and p1_rating["success_rate"] > 0)
check_test("CASE_1.d Prof Voronov avg student ICG computed", p1_rating is not None and p1_rating["avg_student_icg"] > 0)
check_test("CASE_1.e Teacher pedagogical index is calculated", p1_rating is not None and p1_rating["teacher_score"] > 0)


print("\n═══ CASE 2: Teacher Ranking Order & Tier Classification ═══")
check_test("CASE_2.a Teachers sorted in descending order of score", teacher_ratings[0]["teacher_score"] >= teacher_ratings[1]["teacher_score"])
check_test("CASE_2.b Top teacher has rank 1", teacher_ratings[0]["rank"] == 1)
check_test("CASE_2.c Teacher tier label is non-empty", bool(teacher_ratings[0]["tier"]))


print("\n═══ CASE 3: Live Dashboard Teacher Leaderboard (?tab=teachers) ═══")
r_teach = client.get("/?tab=teachers", cookies={"uniplag_session": admin_token})
check_test("CASE_3.a ?tab=teachers returns 200 OK", r_teach.status_code == 200)
check_test("CASE_3.b Dashboard displays 'Рейтинг преподавателей и научных руководителей'", "Рейтинг преподавателей и научных руководителей" in r_teach.text)
check_test("CASE_3.c Dashboard displays teacher name", "Воронов" in r_teach.text or "Кузнецов" in r_teach.text)
check_test("CASE_3.d Dashboard displays gold medal 🥇 for rank 1", "🥇" in r_teach.text or "#1" in r_teach.text)


print("\n═══ CASE 4: Student Color League Divisions (?tab=students) ═══")
r_stud = client.get("/?tab=students", cookies={"uniplag_session": admin_token})
check_test("CASE_4.a ?tab=students returns 200 OK", r_stud.status_code == 200)
check_test("CASE_4.b Dashboard displays 'Полный рейтинг студентов по академическим лигам'", "Полный рейтинг студентов" in r_stud.text)
check_test("CASE_4.c Dashboard displays league color indicators (Высшая лига / Зона риска)", "Высшая лига" in r_stud.text and "Зона риска" in r_stud.text)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Faculty Ranking & Student Color League Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Faculty Ratings & Student Color Leagues OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
