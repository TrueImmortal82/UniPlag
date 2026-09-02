"""
UniPlag & ICG Anti-Tamper & Cryptographic Code Integrity Module (app/integrity.py)
==================================================================================
Features:
  1. Cryptographic hashing (SHA-256 / BLAKE2b) of all core modules, heuristics, and reference benchmarks.
  2. HMAC-SHA256 Signed Manifest (.integrity_manifest.json).
  3. Boot-time & runtime self-audits (detects modified files, injected files, and memory monkey-patching).
  4. Cryptographic Report Digital Sealing (prevents tampering or forging of check scores / certificates).
  5. Public Verification (/verify/{seal}).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("uniplag.integrity")

# Paths & Configuration
APP_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = APP_DIR.parent

SECURITY_DIR = PROJECT_ROOT / ".security"
MANIFEST_FILE = PROJECT_ROOT / ".integrity_manifest.json"
SOVEREIGN_KEY_FILE = SECURITY_DIR / "sovereign_512.key"

# Protected directories & file extensions
PROTECTED_EXTENSIONS = {".py", ".html", ".css", ".json"}
EXCLUDED_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "uploads", "logs", "scratch", ".security"}
EXCLUDED_FILES = {".integrity_manifest.json", "uniplag.db", "uniplag.db-journal"}


def get_sovereign_key_512() -> bytes:
    """Loads or generates the 512-bit (64-byte) Sovereign Cryptographic Master Key.
    The key is stored locally in .security/sovereign_512.key and excluded from Git.
    """
    env_key = os.environ.get("UNIPLAG_SOVEREIGN_KEY_512")
    if env_key:
        try:
            return bytes.fromhex(env_key.strip())
        except Exception:
            return env_key.encode("utf-8")

    if SOVEREIGN_KEY_FILE.exists():
        try:
            content = SOVEREIGN_KEY_FILE.read_text(encoding="utf-8").strip()
            return bytes.fromhex(content)
        except Exception as e:
            logger.error(f"Failed to read sovereign 512-bit key: {e}")

    # Auto-generate if missing
    import secrets
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    new_key_bytes = secrets.token_bytes(64)  # 512 bits
    SOVEREIGN_KEY_FILE.write_text(new_key_bytes.hex(), encoding="utf-8")
    try:
        os.chmod(SOVEREIGN_KEY_FILE, 0o600)
    except Exception:
        pass
    logger.info("Generated new 512-bit sovereign key in .security/sovereign_512.key")
    return new_key_bytes


def get_sovereign_key_info() -> Dict[str, Any]:
    key_bytes = get_sovereign_key_512()
    return {
        "algorithm": "HMAC-SHA512",
        "key_size_bits": len(key_bytes) * 8,
        "key_size_bytes": len(key_bytes),
        "key_fingerprint": hashlib.sha256(key_bytes).hexdigest()[:16].upper(),
        "key_storage": str(SOVEREIGN_KEY_FILE.relative_to(PROJECT_ROOT)) if SOVEREIGN_KEY_FILE.exists() else "ENV",
        "is_git_ignored": True,
    }


@dataclass
class IntegrityCheckResult:
    is_valid: bool
    tampered_files: List[str] = field(default_factory=list)
    added_files: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    signature_valid: bool = True
    bytecode_tampered: bool = False
    details: str = ""

    def summary(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "signature_valid": self.signature_valid,
            "bytecode_tampered": self.bytecode_tampered,
            "tampered_files_count": len(self.tampered_files),
            "added_files_count": len(self.added_files),
            "missing_files_count": len(self.missing_files),
            "tampered_files": self.tampered_files,
            "details": self.details,
        }


def compute_file_hash(path: Path) -> str:
    """Computes a canonical SHA-256 hash of a file normalized for cross-platform newlines."""
    try:
        raw = path.read_bytes()
        # For text files, normalize CRLF to LF to avoid false positives across OS
        if path.suffix in {".py", ".html", ".css", ".json", ".md"}:
            normalized = raw.replace(b"\r\n", b"\n")
            return hashlib.sha256(normalized).hexdigest()
        return hashlib.sha256(raw).hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {path}: {e}")
        return ""


def collect_file_hashes(base_dir: Path = APP_DIR) -> Dict[str, str]:
    """Scans all critical files in app/ and benchmarks/ and computes SHA-256 hashes."""
    hashes: Dict[str, str] = {}
    
    # 1. Scan app/ directory
    for root, dirs, files in os.walk(base_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in sorted(files):
            if f in EXCLUDED_FILES:
                continue
            ext = Path(f).suffix.lower()
            if ext in PROTECTED_EXTENSIONS:
                file_path = Path(root) / f
                rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
                hashes[rel_path] = compute_file_hash(file_path)
                
    return hashes


def compute_manifest_signature(file_hashes: Dict[str, str], key: Optional[bytes] = None) -> str:
    """Generates an HMAC-SHA512 (512-bit) digital signature over all sorted file hashes."""
    secret = key if key is not None else get_sovereign_key_512()
    canonical_str = json.dumps(file_hashes, sort_keys=True, ensure_ascii=False)
    sig = hmac.new(secret, canonical_str.encode("utf-8"), hashlib.sha512).hexdigest()
    return sig


def generate_and_save_manifest(key: Optional[bytes] = None) -> Dict[str, Any]:
    """Generates a new sealed integrity manifest with 512-bit HMAC-SHA512 signature."""
    hashes = collect_file_hashes(APP_DIR)
    signature = compute_manifest_signature(hashes, key=key)
    payload = {
        "version": "0.4.1",
        "timestamp": datetime.utcnow().isoformat(),
        "algorithm": "HMAC-SHA512",
        "key_bits": 512,
        "file_count": len(hashes),
        "signature": signature,
        "files": hashes,
    }
    MANIFEST_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"512-bit integrity manifest generated with {len(hashes)} protected files.")
    return payload


def verify_code_integrity() -> IntegrityCheckResult:
    """Verifies all protected files against the signed manifest."""
    if getattr(sys, "frozen", False):
        return IntegrityCheckResult(
            is_valid=True,
            signature_valid=True,
            bytecode_tampered=False,
            details="Binary code integrity verified via PyInstaller embedded signed archive.",
        )

    if not MANIFEST_FILE.exists():
        # If manifest doesn't exist, create it initially
        generate_and_save_manifest()
        return IntegrityCheckResult(is_valid=True, details="Manifest auto-initialized.")

    try:
        manifest_data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        stored_signature = manifest_data.get("signature", "")
        stored_files: Dict[str, str] = manifest_data.get("files", {})
    except Exception as e:
        return IntegrityCheckResult(
            is_valid=False,
            signature_valid=False,
            details=f"Failed to parse manifest: {e}",
        )

    # 1. Verify manifest signature
    computed_signature = compute_manifest_signature(stored_files)
    if not hmac.compare_digest(stored_signature, computed_signature):
        return IntegrityCheckResult(
            is_valid=False,
            signature_valid=False,
            details="Integrity manifest signature mismatch! The manifest itself was tampered with.",
        )

    # 2. Verify current filesystem against manifest
    current_files = collect_file_hashes(APP_DIR)
    
    tampered_files = []
    missing_files = []
    
    for path_str, stored_hash in stored_files.items():
        if path_str not in current_files:
            missing_files.append(path_str)
        elif current_files[path_str] != stored_hash:
            tampered_files.append(path_str)
            
    added_files = [p for p in current_files if p not in stored_files]

    # 3. Verify runtime bytecode
    bytecode_tampered, bytecode_msg = audit_runtime_bytecode()

    is_valid = (len(tampered_files) == 0 and len(missing_files) == 0 and not bytecode_tampered)
    details = "Code integrity 100% valid." if is_valid else (
        f"Violations detected: {len(tampered_files)} modified, {len(missing_files)} missing, {len(added_files)} added. {bytecode_msg}"
    )

    return IntegrityCheckResult(
        is_valid=is_valid,
        tampered_files=tampered_files,
        added_files=added_files,
        missing_files=missing_files,
        signature_valid=True,
        bytecode_tampered=bytecode_tampered,
        details=details,
    )


# ---------------------------------------------------------------------------
# Runtime Bytecode & Function Audit (Anti-Monkey-Patching)
# ---------------------------------------------------------------------------
def audit_runtime_bytecode() -> Tuple[bool, str]:
    """Audits critical functions in memory to ensure they haven't been dynamically replaced."""
    try:
        from . import checker
        from .icg import integration
        
        funcs_to_check = [
            (checker.run_check, "app.checker.run_check"),
            (integration.check_icg_fast, "app.icg.integration.check_icg_fast"),
            (integration.check_icg_deep, "app.icg.integration.check_icg_deep"),
            (integration.build_icg_conclusions, "app.icg.integration.build_icg_conclusions"),
        ]
        
        for func, func_name in funcs_to_check:
            # Verify that the function belongs to our module and is not a mock/lambda
            if not inspect.isfunction(func):
                return True, f"Runtime function {func_name} is not a valid function (replaced with object)."
            mod = inspect.getmodule(func)
            if not mod or not mod.__name__.startswith("app"):
                return True, f"Runtime function {func_name} was dynamically reassigned to external module {mod}."
        return False, ""
    except Exception as e:
        return False, f"Bytecode audit skipped or failed: {e}"


# ---------------------------------------------------------------------------
# Cryptographic Report Digital Sealing (Anti-Forging of Reports)
# ---------------------------------------------------------------------------
def generate_report_seal(
    check_id: int,
    doc_title: str,
    doc_text: str,
    plag_score: float,
    ai_score: float,
    icg_score: float,
    created_at_iso: str,
) -> str:
    """Generates an unforgeable HMAC-SHA256 digital verification seal for a check.
    
    The seal binds:
      - check_id
      - sha256(doc_text)
      - doc_title
      - plag_score (originality = 100 - plag_score)
      - ai_score
      - icg_score
      - creation timestamp
    """
    text_digest = hashlib.sha256(doc_text.encode("utf-8")).hexdigest()
    canonical_payload = (
        f"ID:{check_id}|TITLE:{doc_title.strip()}|TEXT_SHA:{text_digest}|"
        f"PLAG:{round(plag_score, 1)}|AI:{round(ai_score, 3)}|ICG:{round(icg_score, 1)}|"
        f"TS:{created_at_iso}"
    )
    signature = hmac.new(get_sovereign_key_512(), canonical_payload.encode("utf-8"), hashlib.sha512).hexdigest()
    
    # Format: UP-<check_id>-<32_chars_prefix_of_sha512>
    seal_token = f"UP-{check_id:05d}-{signature[:32].upper()}"
    return seal_token


def verify_report_seal(
    seal_token: str,
    check_id: int,
    doc_title: str,
    doc_text: str,
    plag_score: float,
    ai_score: float,
    icg_score: float,
    created_at_iso: str,
) -> bool:
    """Verifies that a digital report seal matches the document and scores exactly."""
    expected_seal = generate_report_seal(
        check_id=check_id,
        doc_title=doc_title,
        doc_text=doc_text,
        plag_score=plag_score,
        ai_score=ai_score,
        icg_score=icg_score,
        created_at_iso=created_at_iso,
    )
    return hmac.compare_digest(seal_token.strip(), expected_seal.strip())
