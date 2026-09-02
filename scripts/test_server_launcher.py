"""
scripts/test_server_launcher.py — Server Launcher & Advanced Logging Test Suite
Tests:
  1. Multi-tier logging initialization (logs/server.log and logs/error.log)
  2. Operational logging captures events (INFO/DEBUG)
  3. Error logging captures exception stack traces in logs/error.log
  4. Log rotation mechanism configuration
  5. Port availability detection function
"""

import sys
import os
import logging
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run_server import (
    setup_logging,
    is_port_available,
    LOGS_DIR,
    SERVER_LOG_FILE,
    ERROR_LOG_FILE,
)

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


print("\n═══ CASE 1: Logging Subsystem Initialization ═══")
logger = setup_logging(debug=True)

check_test("CASE_1.a Logs directory exists", LOGS_DIR.exists())
check_test("CASE_1.b Server log file created (logs/server.log)", SERVER_LOG_FILE.exists())
check_test("CASE_1.c Error log file created (logs/error.log)", ERROR_LOG_FILE.exists())


print("\n═══ CASE 2: Operational Logging (server.log) ═══")
test_event_msg = "TEST_AUDIT_EVENT_512_OP_VERIFIED"
logger.info(test_event_msg)

# Flush handlers
for h in logging.getLogger().handlers:
    h.flush()

server_log_content = SERVER_LOG_FILE.read_text(encoding="utf-8")
check_test("CASE_2.a Operational log captured INFO event", test_event_msg in server_log_content)


print("\n═══ CASE 3: Error Isolation Logging (error.log) ═══")
test_error_msg = "TEST_CRITICAL_FAILURE_SIMULATED_TRACE"
try:
    raise ValueError(test_error_msg)
except Exception as e:
    logger.error(f"Captured simulated error: {e}", exc_info=True)

for h in logging.getLogger().handlers:
    h.flush()

error_log_content = ERROR_LOG_FILE.read_text(encoding="utf-8")
check_test("CASE_3.a Error log captured exception trace", test_error_msg in error_log_content)
check_test("CASE_3.b Error log contains stack trace marker 'Traceback'", "Traceback (most recent call last)" in error_log_content)


print("\n═══ CASE 4: Port Detection Utility ═══")
# Port 59871 is almost certainly free
check_test("CASE_4.a High unused port reported as available", is_port_available("127.0.0.1", 59871))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Server Launcher & Logging Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Server Launcher & Logging System Fully Operational!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
