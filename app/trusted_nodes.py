"""
UniPlag & ICG Trusted Developer Nodes Subsystem (app/trusted_nodes.py)
======================================================================
Manages hardware & machine fingerprinting, cryptographic authorization of developer
workstations via the Sovereign 512-bit Master Key, and runtime node authentication.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import platform
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .integrity import SECURITY_DIR, get_sovereign_key_512

logger = logging.getLogger("uniplag.trusted_nodes")

TRUSTED_NODES_FILE = SECURITY_DIR / "trusted_developers.json"
NODE_ID_CACHE_FILE = SECURITY_DIR / "node_identity.json"


@dataclass
class MachineFingerprint:
    node_id: str
    hostname: str
    os_name: str
    os_release: str
    machine_arch: str
    system_user: str
    hardware_mac: str

    def canonical_string(self) -> str:
        return (
            f"NODE_ID:{self.node_id}|HOST:{self.hostname}|OS:{self.os_name}|"
            f"REL:{self.os_release}|ARCH:{self.machine_arch}|USER:{self.system_user}|"
            f"MAC:{self.hardware_mac}"
        )


@dataclass
class TrustedDeveloperRecord:
    node_id: str
    hostname: str
    developer_name: str
    machine_alias: str
    authorized_roles: List[str]
    added_at: str
    fingerprint_hash: str
    signature_512: str
    is_active: bool = True


def get_current_machine_fingerprint() -> MachineFingerprint:
    """Extracts hardware and environment identifiers to build a persistent machine fingerprint."""
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Persistent Node ID
    if NODE_ID_CACHE_FILE.exists():
        try:
            cached_data = json.loads(NODE_ID_CACHE_FILE.read_text(encoding="utf-8"))
            persisted_uuid = cached_data.get("node_id", "")
        except Exception:
            persisted_uuid = ""
    else:
        persisted_uuid = ""

    if not persisted_uuid:
        # Generate persistent machine UUID
        raw_seed = f"{platform.node()}-{uuid.getnode()}-{os.environ.get('USERNAME', '')}-{platform.processor()}"
        persisted_uuid = "NODE-" + hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()[:24].upper()
        NODE_ID_CACHE_FILE.write_text(json.dumps({"node_id": persisted_uuid, "created_at": datetime.utcnow().isoformat()}), encoding="utf-8")

    hostname = platform.node() or "UNKNOWN_HOST"
    os_name = platform.system() or "UNKNOWN_OS"
    os_release = f"{platform.release()} ({platform.version()})"
    machine_arch = platform.machine() or "x86_64"
    system_user = os.environ.get("USERNAME") or os.environ.get("USER") or "User"
    hardware_mac = hex(uuid.getnode())

    return MachineFingerprint(
        node_id=persisted_uuid,
        hostname=hostname,
        os_name=os_name,
        os_release=os_release,
        machine_arch=machine_arch,
        system_user=system_user,
        hardware_mac=hardware_mac,
    )


def compute_node_signature_512(fp: MachineFingerprint, dev_name: str, roles: List[str], key: Optional[bytes] = None) -> Tuple[str, str]:
    """Generates 512-bit HMAC-SHA512 signature for a trusted developer machine."""
    secret = key if key is not None else get_sovereign_key_512()
    canonical = fp.canonical_string()
    fp_hash = hashlib.sha512(canonical.encode("utf-8")).hexdigest()
    
    auth_payload = f"FP_HASH:{fp_hash}|DEV:{dev_name.strip()}|ROLES:{','.join(sorted(roles))}"
    sig_512 = hmac.new(secret, auth_payload.encode("utf-8"), hashlib.sha512).hexdigest()
    return fp_hash, sig_512


def register_current_machine_as_trusted(
    developer_name: str = "Vlad (Primary Architect & Sovereign Developer)",
    machine_alias: str = "Primary Dev Workstation (Desktop)",
    roles: Optional[List[str]] = None,
    key_override: Optional[bytes] = None,
) -> TrustedDeveloperRecord:
    """Registers the current workstation as an authorized, cryptographically signed trusted developer machine."""
    if roles is None:
        roles = ["SOVEREIGN_ARCHITECT", "CORE_DEV", "INTEGRITY_SEALER"]

    fp = get_current_machine_fingerprint()
    fp_hash, sig_512 = compute_node_signature_512(fp, developer_name, roles, key=key_override)

    record = TrustedDeveloperRecord(
        node_id=fp.node_id,
        hostname=fp.hostname,
        developer_name=developer_name.strip(),
        machine_alias=machine_alias.strip(),
        authorized_roles=roles,
        added_at=datetime.utcnow().isoformat(),
        fingerprint_hash=fp_hash,
        signature_512=sig_512,
        is_active=True,
    )

    # Update trusted nodes registry
    nodes = list_trusted_developers()
    # Replace existing entry for this node_id or append
    nodes = [n for n in nodes if n.node_id != record.node_id]
    nodes.append(record)

    SECURITY_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.0",
        "algorithm": "HMAC-SHA512",
        "updated_at": datetime.utcnow().isoformat(),
        "trusted_nodes": [asdict(n) for n in nodes],
    }
    TRUSTED_NODES_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Registered machine {fp.hostname} ({fp.node_id}) as trusted developer.")
    return record


def list_trusted_developers() -> List[TrustedDeveloperRecord]:
    """Reads all registered trusted developer workstations."""
    if not TRUSTED_NODES_FILE.exists():
        return []
    try:
        data = json.loads(TRUSTED_NODES_FILE.read_text(encoding="utf-8"))
        raw_list = data.get("trusted_nodes", [])
        return [TrustedDeveloperRecord(**item) for item in raw_list]
    except Exception as e:
        logger.error(f"Failed to read trusted developers registry: {e}")
        return []


def is_current_machine_trusted(key_override: Optional[bytes] = None) -> Tuple[bool, Optional[TrustedDeveloperRecord], str]:
    """Verifies whether the current running machine is in the trusted developer registry with a valid 512-bit signature."""
    fp = get_current_machine_fingerprint()
    records = list_trusted_developers()
    
    matching = next((r for r in records if r.node_id == fp.node_id and r.is_active), None)
    if not matching:
        return False, None, f"Current machine (ID: {fp.node_id}, Host: {fp.hostname}) is not in trusted developers registry."

    # Validate 512-bit cryptographic signature
    expected_fp_hash, expected_sig = compute_node_signature_512(fp, matching.developer_name, matching.authorized_roles, key=key_override)
    
    if not hmac.compare_digest(matching.signature_512, expected_sig):
        return False, matching, "Cryptographic signature mismatch! Machine parameters or credentials were artificially modified."

    return True, matching, f"Machine authenticated: {matching.developer_name} ({matching.machine_alias})"
