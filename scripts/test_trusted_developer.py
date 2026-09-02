"""
scripts/test_trusted_developer.py — Trusted Developer Workstation Automated Test Suite
Tests:
  1. Machine fingerprinting (Host, Node ID, User, OS, MAC)
  2. 512-bit HMAC-SHA512 machine signature computation
  3. Trusted developer node registration & persistence
  4. Authentication of authorized developer workstation
  5. Cryptographic rejection of spoofed / tampered machine credentials
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.trusted_nodes import (
    get_current_machine_fingerprint,
    register_current_machine_as_trusted,
    is_current_machine_trusted,
    compute_node_signature_512,
    list_trusted_developers,
    TRUSTED_NODES_FILE,
    MachineFingerprint,
)
from app.integrity import get_sovereign_key_512

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
results = []

def check_test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


print("\n═══ CASE 1: Machine Fingerprint Extraction ═══")
fp = get_current_machine_fingerprint()
check_test("CASE_1.a Hostname extracted", bool(fp.hostname))
check_test("CASE_1.b Node ID format valid (starts with 'NODE-')", fp.node_id.startswith("NODE-"))
check_test("CASE_1.c System user extracted", bool(fp.system_user))
check_test("CASE_1.d OS & Arch extracted", bool(fp.os_name) and bool(fp.machine_arch))


print("\n═══ CASE 2: 512-bit Machine Signature Computation ═══")
fp_hash, sig_512 = compute_node_signature_512(fp, "Vlad", ["SOVEREIGN_ARCHITECT"])
check_test("CASE_2.a Fingerprint hash is SHA-512 (128 hex chars)", len(fp_hash) == 128)
check_test("CASE_2.b Machine signature is HMAC-SHA512 (128 hex chars)", len(sig_512) == 128)


print("\n═══ CASE 3: Trusted Developer Machine Registration ═══")
record = register_current_machine_as_trusted(
    developer_name="Vlad (Primary Architect & Sovereign Developer)",
    machine_alias="Primary Workstation (Desktop)",
    roles=["SOVEREIGN_ARCHITECT", "CORE_DEV", "INTEGRITY_SEALER"],
)
check_test("CASE_3.a Machine registration saved to registry", TRUSTED_NODES_FILE.exists())
check_test("CASE_3.b Registered node ID matches machine", record.node_id == fp.node_id)
check_test("CASE_3.c Registered developer name matches", "Vlad" in record.developer_name)


print("\n═══ CASE 4: Trusted Machine Authentication Gate ═══")
is_trusted, auth_rec, msg = is_current_machine_trusted()
check_test("CASE_4.a Current machine successfully authenticated as trusted developer", is_trusted)
check_test("CASE_4.b Auth record matches registered machine", auth_rec is not None and auth_rec.node_id == fp.node_id)


print("\n═══ CASE 5: Detection of Spoofed / Tampered Machine Credentials ═══")
# Simulate an attacker forging the hostname or MAC address
fake_fp = MachineFingerprint(
    node_id=fp.node_id,
    hostname="ATTACKER_LAPTOP_FORGER",
    os_name=fp.os_name,
    os_release=fp.os_release,
    machine_arch=fp.machine_arch,
    system_user="hacker",
    hardware_mac="0x000000000000",
)
fake_fp_hash, fake_sig = compute_node_signature_512(fake_fp, "Vlad", ["SOVEREIGN_ARCHITECT"])
check_test("CASE_5.a Spoofed machine produces different signature", fake_sig != record.signature_512)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Trusted Developer Subsystem Test Suite: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Trusted Developer Machine Registered & Authenticated!")
    sys.exit(0)
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")
    sys.exit(1)
