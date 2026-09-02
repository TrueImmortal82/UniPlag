"""
UniPlag & ICG Project Change Consensus & Cryptographic Audit Ledger Module (app/consensus.py)
=============================================================================================
Manages project change governance, proposal validation, cryptographic signing with the
Sovereign 512-bit Master Key, and maintains an immutable chained audit ledger.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .integrity import (
    APP_DIR,
    PROJECT_ROOT,
    SECURITY_DIR,
    MANIFEST_FILE,
    collect_file_hashes,
    compute_manifest_signature,
    generate_and_save_manifest,
    get_sovereign_key_512,
    get_sovereign_key_info,
)

logger = logging.getLogger("uniplag.consensus")

LEDGER_FILE = SECURITY_DIR / "audit_ledger.jsonl"


@dataclass
class ChangeDelta:
    modified_files: List[str] = field(default_factory=list)
    added_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    has_changes: bool = False
    total_delta_count: int = 0
    current_file_count: int = 0
    signed_file_count: int = 0


@dataclass
class LedgerBlock:
    block_index: int
    timestamp: str
    author: str
    description: str
    file_count: int
    manifest_signature: str
    prev_block_hash: str
    block_hash: str = ""

    def compute_hash(self) -> str:
        canonical = (
            f"INDEX:{self.block_index}|TS:{self.timestamp}|AUTHOR:{self.author.strip()}|"
            f"DESC:{self.description.strip()}|FILES:{self.file_count}|"
            f"SIG:{self.manifest_signature}|PREV:{self.prev_block_hash}"
        )
        return hashlib.sha512(canonical.encode("utf-8")).hexdigest()


def inspect_pending_changes() -> ChangeDelta:
    """Compares the current codebase state against the signed 512-bit manifest."""
    current_hashes = collect_file_hashes(APP_DIR)
    
    if not MANIFEST_FILE.exists():
        return ChangeDelta(
            added_files=list(current_hashes.keys()),
            has_changes=True,
            total_delta_count=len(current_hashes),
            current_file_count=len(current_hashes),
            signed_file_count=0,
        )

    try:
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        stored_files: Dict[str, str] = manifest.get("files", {})
    except Exception as e:
        logger.error(f"Error reading manifest: {e}")
        stored_files = {}

    modified = []
    removed = []
    
    for path, stored_hash in stored_files.items():
        if path not in current_hashes:
            removed.append(path)
        elif current_hashes[path] != stored_hash:
            modified.append(path)
            
    added = [p for p in current_hashes if p not in stored_files]
    
    has_changes = bool(modified or added or removed)
    total_delta = len(modified) + len(added) + len(removed)
    
    return ChangeDelta(
        modified_files=sorted(modified),
        added_files=sorted(added),
        removed_files=sorted(removed),
        has_changes=has_changes,
        total_delta_count=total_delta,
        current_file_count=len(current_hashes),
        signed_file_count=len(stored_files),
    )


def read_audit_ledger() -> List[LedgerBlock]:
    """Reads all blocks from the audit ledger."""
    if not LEDGER_FILE.exists():
        return []
    
    blocks = []
    for line in LEDGER_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            blocks.append(LedgerBlock(**d))
        except Exception as e:
            logger.error(f"Corrupt ledger line: {e}")
    return blocks


def verify_audit_ledger() -> Tuple[bool, str]:
    """Cryptographically verifies the blockchain hash continuity of the audit ledger."""
    blocks = read_audit_ledger()
    if not blocks:
        return True, "Ledger is empty (no previous releases recorded)."
    
    prev_hash = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"
    for i, b in enumerate(blocks):
        if b.block_index != i + 1:
            return False, f"Block index discontinuity at position {i}: expected {i+1}, found {b.block_index}"
        if b.prev_block_hash != prev_hash:
            return False, f"Broken cryptographic chain at block {b.block_index}: prev_hash mismatch!"
        expected_hash = b.compute_hash()
        if b.block_hash != expected_hash:
            return False, f"Tampered block hash at block {b.block_index}!"
        prev_hash = b.block_hash
        
    return True, f"Ledger integrity verified: {len(blocks)} chained blocks valid."


def approve_and_seal_changes(author: str, description: str, key_override: Optional[bytes] = None) -> LedgerBlock:
    """Approves all current changes, generates a new 512-bit HMAC-SHA512 manifest,
    and appends a new block to the chained audit ledger.
    """
    key = key_override if key_override is not None else get_sovereign_key_512()
    
    # 1. Update & sign manifest
    manifest = generate_and_save_manifest(key=key)
    manifest_sig = manifest["signature"]
    file_count = manifest["file_count"]
    
    # 2. Get last block hash
    blocks = read_audit_ledger()
    if blocks:
        prev_hash = blocks[-1].block_hash
        next_index = len(blocks) + 1
    else:
        prev_hash = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"
        next_index = 1
        
    new_block = LedgerBlock(
        block_index=next_index,
        timestamp=datetime.utcnow().isoformat(),
        author=author.strip() or "Architect",
        description=description.strip() or "Approved changes",
        file_count=file_count,
        manifest_signature=manifest_sig,
        prev_block_hash=prev_hash,
    )
    new_block.block_hash = new_block.compute_hash()
    
    # 3. Append to ledger file
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(new_block), ensure_ascii=False) + "\n")
        
    logger.info(f"Block #{new_block.block_index} recorded in audit ledger: {new_block.description}")
    return new_block
