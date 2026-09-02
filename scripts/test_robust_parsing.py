"""
scripts/test_robust_parsing.py — Text Extraction & File Support Test Suite
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parsing import extract_text

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition

tmp_dir = Path("tmp_test_parsing")
tmp_dir.mkdir(exist_ok=True)

try:
    # 1. UTF-8 TXT
    f_utf8 = tmp_dir / "test_utf8.txt"
    f_utf8.write_text("Тестовый текст в кодировке UTF-8 с русскими буквами.", encoding="utf-8")
    t1 = extract_text(f_utf8)
    check_test("CASE_1.a UTF-8 TXT extraction", "UTF-8" in t1 and "русскими" in t1)

    # 2. CP1251 TXT
    f_cp1251 = tmp_dir / "test_cp1251.txt"
    f_cp1251.write_bytes("Текст в старой русской кодировке CP1251.".encode("cp1251"))
    t2 = extract_text(f_cp1251)
    check_test("CASE_1.b CP1251 TXT extraction", "CP1251" in t2 and "русской" in t2)

    # 3. RTF
    f_rtf = tmp_dir / "test.rtf"
    rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}} \f0\fs24 \'d2\'e5\'ea\'f1\'f2 \'e8\'e7 RTF \'f4\'e0\'e9\'eb\'e0. \par}"
    f_rtf.write_bytes(rtf_content.encode("latin1"))
    t3 = extract_text(f_rtf)
    check_test("CASE_1.c RTF extraction", "Текст" in t3 and "RTF" in t3)

    # 4. DOCX
    import docx
    d = docx.Document()
    d.add_paragraph("Параграф научной работы в формате DOCX.")
    f_docx = tmp_dir / "test.docx"
    d.save(str(f_docx))
    t4 = extract_text(f_docx)
    check_test("CASE_1.d DOCX extraction", "научной работы" in t4)

    # 5. Simulated legacy .DOC binary stream
    f_doc = tmp_dir / "test.doc"
    raw_doc = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + "Текст старого документа Word 97".encode("utf-16le")
    f_doc.write_bytes(raw_doc)
    t5 = extract_text(f_doc)
    check_test("CASE_1.e Legacy binary .DOC extraction fallback", "Текст старого документа" in t5)

    # 6. Empty file
    f_empty = tmp_dir / "empty.txt"
    f_empty.write_bytes(b"")
    t6 = extract_text(f_empty)
    check_test("CASE_1.f Empty file returns empty string safely", t6 == "")

finally:
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Parsing & Text Extraction Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Text Extraction OPERATIONAL across all formats!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
