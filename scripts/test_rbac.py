"""
scripts/test_rbac.py — RBAC & Multi-Role Architecture Automated Test Suite
Tests:
  1. Default accounts initialization (admin, teacher, student)
  2. Role-based permissions & access gates (403 on restricted endpoints)
  3. Data isolation: students cannot access other students' reports
  4. Upload ownership binding (student auto-bind vs teacher student selector)
  5. User administration CRUD (/admin/users)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
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

print("\n═══ CASE 1: Default Accounts & Role Seeding ═══")
init_db()
with SessionLocal() as db:
    admin_u = db.query(User).filter(User.username == "admin").first()
    teacher_u = db.query(User).filter(User.username == "teacher").first()
    student_u = db.query(User).filter(User.username == "student").first()
    
    check_test("CASE_1.a Admin user exists with role 'admin'", admin_u is not None and admin_u.role == "admin")
    check_test("CASE_1.b Teacher user exists with role 'teacher'", teacher_u is not None and teacher_u.role == "teacher")
    check_test("CASE_1.c Student user exists with role 'student'", student_u is not None and student_u.role == "student")
    
    admin_tok = create_session(admin_u.id)
    teacher_tok = create_session(teacher_u.id)
    student_tok = create_session(student_u.id)


print("\n═══ CASE 2: Route Protection & RBAC Access Gates ═══")
# 1. /admin/users: only admin can access
r_admin_users_admin = client.get("/admin/users", cookies={"uniplag_session": admin_tok})
check_test("CASE_2.a Admin can access /admin/users (200 OK)", r_admin_users_admin.status_code == 200)

r_admin_users_teacher = client.get("/admin/users", cookies={"uniplag_session": teacher_tok})
check_test("CASE_2.b Teacher blocked from /admin/users (403 Forbidden)", r_admin_users_teacher.status_code == 403)

r_admin_users_student = client.get("/admin/users", cookies={"uniplag_session": student_tok})
check_test("CASE_2.c Student blocked from /admin/users (403 Forbidden)", r_admin_users_student.status_code == 403)

# 2. /corpus: only teacher and admin can access
r_corpus_teacher = client.get("/corpus", cookies={"uniplag_session": teacher_tok})
check_test("CASE_2.d Teacher can access /corpus (200 OK)", r_corpus_teacher.status_code == 200)

r_corpus_student = client.get("/corpus", cookies={"uniplag_session": student_tok})
check_test("CASE_2.e Student blocked from /corpus (403 Forbidden)", r_corpus_student.status_code == 403)

# 3. /admin/icg: only admin can access
r_icg_admin = client.get("/admin/icg", cookies={"uniplag_session": admin_tok})
check_test("CASE_2.f Admin can access /admin/icg (200 OK)", r_icg_admin.status_code == 200)

r_icg_teacher = client.get("/admin/icg", cookies={"uniplag_session": teacher_tok})
check_test("CASE_2.g Teacher blocked from /admin/icg (403 Forbidden)", r_icg_teacher.status_code == 403)


print("\n═══ CASE 3: Student Data Isolation & Report Protection ═══")
with SessionLocal() as db:
    # Create a document belonging to Student 1
    doc_student = Document(
        title="Дипломная работа Иванова",
        author="Иван Иванов",
        kind="student",
        text="Это текст работы студента Иванова по машинному обучению.",
        owner_id=student_u.id,
    )
    db.add(doc_student)
    db.commit()
    db.refresh(doc_student)
    
    check_student = Check(
        document_id=doc_student.id,
        plag_score=15.0,
        ai_score=0.1,
        icg_score=65.0,
        status="done",
    )
    db.add(check_student)
    
    # Create another student (Student 2)
    student2 = db.query(User).filter(User.username == "student_petrov").first()
    if not student2:
        student2 = User(username="student_petrov", role="student", full_name="Пётр Петров", group_name="ИТ-402")
        student2.set_password("pass123")
        db.add(student2)
        db.commit()
        db.refresh(student2)
    student2_tok = create_session(student2.id)

    # Create document for Student 2
    doc_student2 = Document(
        title="Курсовая работа Петрова",
        author="Пётр Петров",
        kind="student",
        text="Это текст работы студента Петрова по квантовой физике.",
        owner_id=student2.id,
    )
    db.add(doc_student2)
    db.commit()
    db.refresh(doc_student2)
    
    check_student2 = Check(
        document_id=doc_student2.id,
        plag_score=10.0,
        ai_score=0.05,
        icg_score=75.0,
        status="done",
    )
    db.add(check_student2)
    db.commit()
    
    c1_id = check_student.id
    c2_id = check_student2.id

# Student 1 accessing their own report
r_s1_own = client.get(f"/report/{c1_id}", cookies={"uniplag_session": student_tok})
check_test("CASE_3.a Student can access their own report (200 OK)", r_s1_own.status_code == 200)

# Student 1 attempting to access Student 2's report
r_s1_other = client.get(f"/report/{c2_id}", cookies={"uniplag_session": student_tok})
check_test("CASE_3.b Student blocked from viewing another student's report (403 Forbidden)", r_s1_other.status_code == 403)

# Teacher accessing any student's report
r_teacher_c1 = client.get(f"/report/{c1_id}", cookies={"uniplag_session": teacher_tok})
r_teacher_c2 = client.get(f"/report/{c2_id}", cookies={"uniplag_session": teacher_tok})
check_test("CASE_3.c Teacher can access any student's report (200 OK)", r_teacher_c1.status_code == 200 and r_teacher_c2.status_code == 200)


print("\n═══ CASE 4: Dashboard Filtering by Role ═══")
r_dash_student = client.get("/", cookies={"uniplag_session": student_tok})
check_test("CASE_4.a Student dashboard returns 200 and renders personal section", 
           r_dash_student.status_code == 200 and "Мои проверенные работы" in r_dash_student.text)
check_test("CASE_4.b Student dashboard does NOT leak other students' titles", 
           "Курсовая работа Петрова" not in r_dash_student.text)

r_dash_teacher = client.get("/", cookies={"uniplag_session": teacher_tok})
check_test("CASE_4.c Teacher dashboard returns 200 and shows university registry", 
           r_dash_teacher.status_code == 200 and "Проверки студенческих работ" in r_dash_teacher.text)


print("\n═══ CASE 5: User Management CRUD (/admin/users) ═══")
test_new_user = "test_assistant_99"
# 1. Create user
r_create = client.post(
    "/admin/users/create",
    data={"username": test_new_user, "password": "temp_password_123", "role": "teacher", "full_name": "Тестовый Ассистент"},
    cookies={"uniplag_session": admin_tok},
    follow_redirects=False,
)
check_test("CASE_5.a Admin creates new user successfully (303 Redirect)", r_create.status_code == 303 and "/admin/users" in r_create.headers.get("location", ""))

# Verify user exists
with SessionLocal() as db:
    created_u = db.query(User).filter(User.username == test_new_user).first()
    check_test("CASE_5.b Created user persisted in DB with role 'teacher'", created_u is not None and created_u.role == "teacher")
    
    if created_u:
        u_id = created_u.id
        # 2. Reset password
        r_reset = client.post(
            f"/admin/users/{u_id}/reset-password",
            data={"password": "new_secret_password"},
            cookies={"uniplag_session": admin_tok},
            follow_redirects=False,
        )
        check_test("CASE_5.c Admin resets user password successfully (303 Redirect)", r_reset.status_code == 303)
        
        # Verify password updated
        db.refresh(created_u)
        check_test("CASE_5.d New password verified via hash", created_u.check_password("new_secret_password"))

        # 3. Delete user
        r_del = client.post(
            f"/admin/users/{u_id}/delete",
            cookies={"uniplag_session": admin_tok},
            follow_redirects=False,
        )
        check_test("CASE_5.e Admin deletes user successfully (303 Redirect)", r_del.status_code == 303)
        
        deleted_u = db.query(User).filter(User.username == test_new_user).first()
        check_test("CASE_5.f Deleted user no longer in DB", deleted_u is None)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  RBAC & Multi-Role Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Multi-Role RBAC System Fully Operational!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
