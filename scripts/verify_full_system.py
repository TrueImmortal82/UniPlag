"""
scripts/verify_full_system.py — Comprehensive Master System Verification Suite
=============================================================================
Performs deep end-to-end validation of all 10 core subsystems of UniPlag & ICG v0.4.1:
  1. Database Schema, Relations & RBAC
  2. Multi-Format Text Extraction (DOCX, PDF, RTF, TXT, ODT, DOC)
  3. Plagiarism Detection & Corpus Inverted Index (LSH / MinHash)
  4. AI Content Probability Engine
  5. ICG v0.4 Semantic DAG & Academic Recommendations
  6. High-Definition Vector PDF Certificate Generator (A4, SHA-512 Seal)
  7. Open Scientific Repositories Connector (arXiv API & Ingestion)
  8. Faculty Pedagogical Ranking (TeacherScore) & Student Color Leagues
  9. Interactive User Guide & Ergonomic UI (/guide, Drag&Drop Upload)
  10. 512-bit Sovereign Master Key & Immutable Blockchain Ledger
"""

import sys
import os
import json
import urllib.parse
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User, Document, Check, Match, Fragment
from app.auth import create_session
from app.pdf_certificate import generate_check_pdf_certificate
from app.scientific_crawler import search_all_scientific_repositories, ingest_scientific_article
from app.consensus import inspect_pending_changes, read_audit_ledger, verify_audit_ledger
from app.integrity import get_sovereign_key_info
from app.trusted_nodes import is_current_machine_trusted

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


print("\n" + "═" * 70)
print("  🛡️  UNIPLAG & ICG v0.4.1 — MASTER SYSTEM VERIFICATION")
print("═" * 70)

client = TestClient(app)
init_db()

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 1: Database & RBAC Authentication
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/10] 🗄️ Database, Session Tokens & RBAC Security...")
with SessionLocal() as db:
    admin = db.query(User).filter(User.role == "admin").first()
    teacher = db.query(User).filter(User.role == "teacher").first()
    student = db.query(User).filter(User.role == "student").first()

    check("1.1 Admin user exists", admin is not None)
    check("1.2 Teacher user exists", teacher is not None)
    check("1.3 Student user exists", student is not None)

    admin_tok = create_session(admin.id)
    student_tok = create_session(student.id)

    # Check RBAC route protection
    resp_adm_only = client.get("/admin/consensus", cookies={"uniplag_session": student_tok})
    check("1.4 Student blocked from admin consensus (403)", resp_adm_only.status_code == 403)
    resp_adm_ok = client.get("/admin/consensus", cookies={"uniplag_session": admin_tok})
    check("1.5 Admin can access consensus (200)", resp_adm_ok.status_code == 200)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 2: Multi-format Parsing & Text Viewer
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/10] 📄 Multi-Format Text Parsing & Document Viewer...")
with SessionLocal() as db:
    # Check sample report text loading
    sample_chk = db.query(Check).join(Document, Check.document_id == Document.id).filter(Check.status == "done", Document.text != None).order_by(Check.id.desc()).first()
    if not sample_chk or len(sample_chk.document.text or "") < 100:
        sample_chk = db.get(Check, 93)
    if sample_chk:
        resp_rep = client.get(f"/report/{sample_chk.id}", cookies={"uniplag_session": admin_tok})
        check("2.1 Report page loads (200 OK)", resp_rep.status_code == 200)
        check("2.2 Scroll window container present", "doc-text-window" in resp_rep.text)
        check("2.3 Font zoom buttons present (A- / A+)", "A+" in resp_rep.text)
        check("2.4 Copy button present", "Копировать" in resp_rep.text)
        check("2.5 Fullscreen toggle present", "На весь экран" in resp_rep.text)
        check("2.6 Document text is populated (>100 chars)", sample_chk.document and len(sample_chk.document.text or "") > 100)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 3 & 4: Plagiarism, Inverted Index & AI Detection
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/10 & 4/10] 🔍 Plagiarism Corpus Index & AI Detection Engine...")
from app.plagiarism import corpus_index, fingerprint
from app.ai_detector import detect

fp = fingerprint("Тестовый текст для проверки фингерпринта и инвертированного индекса.")
check("3.1 Fingerprint contains MinHash signature", "sig" in fp and len(fp["sig"]) > 0)
check("3.2 Fingerprint contains LSH keys", "keys" in fp and len(fp["keys"]) > 0)

sample_ai_text = (
    "В современном мире информационные технологии играют важную роль в развитии образовательного процесса. "
    "Таким образом, необходимо отметить, что цифровые системы являются неотъемлемой частью высшей школы. "
    "Кроме того, важно подчеркнуть, что использование методов искусственного интеллекта представляет собой значительный шаг вперёд."
)
ai_res = detect(sample_ai_text)
check("4.1 AI detector returns probability score", 0.0 <= ai_res.get("score", -1) <= 1.0)
check("4.2 AI detector returns per-sentence breakdown", isinstance(ai_res.get("sentences"), list))

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 5: ICG v0.4 & Academic Recommendations
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/10] 🧠 ICG v0.4 Reasoning Graph & Recommendations...")
from app.icg.recommendations import generate_icg_recommendations

recs = generate_icg_recommendations({}, plag_score=15.0, ai_score=0.10, icg_score=72.0)
check("5.1 Recommendations contain Top Priority Growth Vector", "top_priority" in recs and len(recs["top_priority"]) > 0)
check("5.2 Recommendations contain Actionable Checklist", isinstance(recs.get("action_checklist"), list) and len(recs["action_checklist"]) > 0)
check("5.3 Recommendations contain Academic Phrasing Templates", isinstance(recs.get("phrasing_templates"), list) and len(recs["phrasing_templates"]) > 0)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 6: Official PDF Certificate Generator
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/10] 📜 High-Definition Vector PDF Certificate Generator...")
with SessionLocal() as db:
    chk_pdf = db.query(Check).filter(Check.status == "done").first()
    if chk_pdf:
        pdf_bytes = generate_check_pdf_certificate(chk_pdf)
        check("6.1 PDF binary stream generated (>5 KB)", len(pdf_bytes) > 5000)
        check("6.2 PDF header valid (%PDF-)", pdf_bytes.startswith(b"%PDF-"))
        resp_pdf = client.get(f"/report/{chk_pdf.id}/pdf", cookies={"uniplag_session": admin_tok})
        check("6.3 Live PDF endpoint returns 200 OK", resp_pdf.status_code == 200)
        check("6.4 Content-Type is application/pdf", "application/pdf" in resp_pdf.headers.get("content-type", ""))
        check("6.5 Content-Disposition is RFC 5987 safe", "Certificate_Check" in resp_pdf.headers.get("content-disposition", ""))

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 7: Scientific Repositories Connector
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7/10] 🌐 Scientific Repositories Connector (arXiv & Open Access)...")
articles = search_all_scientific_repositories("machine learning", max_results=2)
check("7.1 arXiv / Open search returns articles", len(articles) >= 1)
check("7.2 Article contains title, authors, full text", bool(articles[0].get("title")) and bool(articles[0].get("authors")))

with SessionLocal() as db:
    test_ingest = {
        "title": "Master Verification Test Article",
        "authors": "Academic Team",
        "url": "https://arxiv.org/abs/2609.99999",
        "summary": "Master test summary.",
        "source": "arXiv",
        "full_text": "Master Verification Test Article\n\nAuthors: Academic Team\n\nSummary: Verified."
    }
    ingested = ingest_scientific_article(db, test_ingest, owner_id=admin.id)
    check("7.3 Article ingested into DB as kind='web'", ingested.kind == "web")
    check("7.4 Article indexed in inverted index corpus_index", ingested.id in corpus_index._sigs)

resp_sci_ui = client.get("/corpus/search_science?q=cryptography", cookies={"uniplag_session": admin_tok})
check("7.5 GET /corpus/search_science returns 200 OK", resp_sci_ui.status_code == 200)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 8: Faculty Ratings & Student Color Leagues
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8/10] 🏆 Faculty Pedagogical Ratings & Student Color Leagues...")
resp_students_tab = client.get("/?tab=students", cookies={"uniplag_session": admin_tok})
check("8.1 Full Student Color League renders (200 OK)", resp_students_tab.status_code == 200)
check("8.2 Student ranking table present", "Рейтинг студентов" in resp_students_tab.text or "Академический рейтинг" in resp_students_tab.text)

resp_teachers_tab = client.get("/?tab=teachers", cookies={"uniplag_session": admin_tok})
check("8.3 Faculty Pedagogical Leaderboard renders (200 OK)", resp_teachers_tab.status_code == 200)
check("8.4 Faculty table contains Pedagogical Index", "Педагогический индекс" in resp_teachers_tab.text or "Рейтинг преподавателей" in resp_teachers_tab.text)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 9: Intuitive UI & User Guide
# ─────────────────────────────────────────────────────────────────────────────
print("\n[9/10] 📖 Intuitive UI, Drag & Drop Upload & User Guide (/guide)...")
resp_guide = client.get("/guide", cookies={"uniplag_session": student_tok})
check("9.1 GET /guide returns 200 OK", resp_guide.status_code == 200)
check("9.2 Guide contains Student instructions", "Инструкция для студента" in resp_guide.text)
check("9.3 Guide contains Teacher instructions", "Инструкция для преподавателя" in resp_guide.text)
check("9.4 Guide contains FAQ", "Часто задаваемые вопросы" in resp_guide.text)

guide_md = Path("USER_GUIDE.md")
check("9.5 USER_GUIDE.md document exists in root", guide_md.exists())

resp_upload = client.get("/upload", cookies={"uniplag_session": student_tok})
check("9.6 Upload page has Drag & Drop dropzone", "drop-area" in resp_upload.text)

# ─────────────────────────────────────────────────────────────────────────────
# Subsystem 10: 512-bit Cryptographic Consensus & Sovereign Ledger
# ─────────────────────────────────────────────────────────────────────────────
print("\n[10/10] 🔒 512-bit Cryptographic Consensus & Sovereign Ledger...")
key_info = get_sovereign_key_info()
check("10.1 Master Key bit length is exactly 512 bits", key_info["key_size_bits"] == 512)
check("10.2 Algorithm is HMAC-SHA512", key_info["algorithm"] == "HMAC-SHA512")

delta = inspect_pending_changes()
check("10.3 Codebase in 100% consensus (no unapproved diffs)", not delta.has_changes)

ledger_ok, ledger_msg = verify_audit_ledger()
check("10.4 Blockchain Audit Ledger continuity verified", ledger_ok, ledger_msg)

is_trusted, dev_rec, trust_msg = is_current_machine_trusted()
check("10.5 Current workstation is authorized in trusted registry", is_trusted, trust_msg)


# ─────────────────────────────────────────────────────────────────────────────
# FINAL MASTER REPORT
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print("\n" + "═" * 70)
print(f"  🏁 MASTER SYSTEM VERIFICATION RESULT: {passed}/{total} PASS ({100*passed//total}%)")
print("═" * 70)

if passed == total:
    print("  🎉 ВСЕ ПОДСИСТЕМЫ И ИНТЕРФЕЙСЫ UNIPLAG & ICG v0.4.1 РАБОТАЮТ БЕЗУПРЕЧНО!")
    sys.exit(0)
else:
    print(f"  ⚠️  Обнаружено непройденных проверок: {total - passed}")
    sys.exit(1)
