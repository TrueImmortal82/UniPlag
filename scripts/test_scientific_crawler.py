"""
scripts/test_scientific_crawler.py — Scientific Repositories Connector Test Suite
Tests:
  1. search_all_scientific_repositories queries articles and returns structured entries
  2. ingest_scientific_article stores paper as kind='web' and indexes in corpus_index
  3. Live endpoint GET /corpus/search_science renders results
  4. Live endpoint POST /corpus/ingest_science adds article and redirects
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, SessionLocal, User, Document
from app.auth import create_session
from app.scientific_crawler import search_all_scientific_repositories, ingest_scientific_article
from app.plagiarism import corpus_index

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

print("\n═══ CASE 1: Scientific Repository Search & Parsing ═══")
articles = search_all_scientific_repositories("cryptography", max_results=3)
check_test("CASE_1.a Search returns article list (>= 1)", len(articles) >= 1)
check_test("CASE_1.b First article has title", bool(articles[0].get("title")))
check_test("CASE_1.c First article has authors", bool(articles[0].get("authors")))
check_test("CASE_1.d First article has full text payload", bool(articles[0].get("full_text")))

print("\n═══ CASE 2: Article Corpus Ingestion & Fingerprinting ═══")
with SessionLocal() as db:
    sample_art = {
        "title": "Quantum Resistance in Post-Quantum Cryptography",
        "authors": "Alice Researcher, Bob Scientist",
        "url": "http://arxiv.org/abs/2501.99999",
        "summary": "This paper analyzes lattice-based cryptographic algorithms for post-quantum resistance.",
        "source": "arXiv",
        "full_text": "Quantum Resistance in Post-Quantum Cryptography\n\nAuthors: Alice Researcher\n\nAbstract: Analysis of lattice algorithms."
    }
    doc = ingest_scientific_article(db, sample_art)
    check_test("CASE_2.a Article saved to DB with kind='web'", doc.kind == "web")
    check_test("CASE_2.b Article indexed in in-memory corpus_index", doc.id in corpus_index._sigs)

print("\n═══ CASE 3: Live UI Endpoints (/corpus/search_science & ingest) ═══")
with SessionLocal() as db:
    admin_u = db.query(User).filter(User.role == "admin").first()
    admin_tok = create_session(admin_u.id)

resp_search = client.get("/corpus/search_science?q=neural", cookies={"uniplag_session": admin_tok})
check_test("CASE_3.a GET /corpus/search_science returns 200 OK", resp_search.status_code == 200)
check_test("CASE_3.b Search page contains search header", "Поиск по открытым научным базам" in resp_search.text)
check_test("CASE_3.c Search page renders '+ В корпус проверок' button", "+ В корпус проверок" in resp_search.text)

resp_ingest = client.post(
    "/corpus/ingest_science",
    data={
        "title": "Live Ingested Science Paper 2026",
        "authors": "Dr. Smith",
        "url": "https://arxiv.org/abs/2601.12345",
        "summary": "Demonstration paper for live corpus integration.",
        "source": "arXiv",
        "q": "neural"
    },
    cookies={"uniplag_session": admin_tok},
    follow_redirects=False
)
check_test("CASE_3.d POST /corpus/ingest_science redirects 303", resp_ingest.status_code == 303)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Scientific Repositories Crawler Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Scientific Repositories Integration OPERATIONAL!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
