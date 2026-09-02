"""
scripts/register_trusted_developer.py — Register Current Workstation as Trusted Developer Node
Cryptographically binds the local machine parameters (Host, Hardware UUID, OS, User)
to a 512-bit signed authorization record in .security/trusted_developers.json.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.trusted_nodes import (
    get_current_machine_fingerprint,
    register_current_machine_as_trusted,
    is_current_machine_trusted,
    list_trusted_developers,
)
from app.integrity import get_sovereign_key_info


def main():
    parser = argparse.ArgumentParser(description="UniPlag Trusted Developer Workstation Registrar")
    parser.add_argument("--name", "-n", default="Vlad (Primary Architect & Sovereign Developer)", help="Developer Full Name / Identity")
    parser.add_argument("--alias", "-a", default="Primary Dev Workstation (Desktop)", help="Human-readable machine alias")
    parser.add_argument("--roles", "-r", nargs="+", default=["SOVEREIGN_ARCHITECT", "CORE_DEV", "INTEGRITY_SEALER"], help="Authorized developer roles")
    parser.add_argument("--status", "-s", action="store_true", help="Display current machine trust status only")
    args = parser.parse_args()

    fp = get_current_machine_fingerprint()
    key_info = get_sovereign_key_info()

    print("\n════════════════════════════════════════════════════════════")
    print("  💻  UniPlag Sovereign Trusted Developer Node Subsystem")
    print("════════════════════════════════════════════════════════════")
    print(f"  🖥️  Machine Hostname:  {fp.hostname}")
    print(f"  🆔  Node Unique ID:    {fp.node_id}")
    print(f"  👤  System User:       {fp.system_user}")
    print(f"  🖧   Hardware Node MAC: {fp.hardware_mac}")
    print(f"  💿  OS / Architecture: {fp.os_name} {fp.os_release} [{fp.machine_arch}]")
    print(f"  🔑  Signing Key:       {key_info['key_size_bits']} bits (HMAC-SHA512)")
    
    is_trusted, record, msg = is_current_machine_trusted()
    
    if args.status:
        if is_trusted and record:
            print(f"\n  🟢 TRUST STATUS: AUTHORIZED TRUSTED DEVELOPER NODE")
            print(f"     Developer: {record.developer_name}")
            print(f"     Alias:     {record.machine_alias}")
            print(f"     Roles:     {', '.join(record.authorized_roles)}")
            print(f"     Signature: {record.signature_512[:32]}... (512-bit HMAC)")
        else:
            print(f"\n  🟡 TRUST STATUS: NOT REGISTERED")
            print(f"     Message: {msg}")
        return

    # Register machine
    print(f"\n  ✍️  Cryptographically signing machine registration with Sovereign 512-bit Key...")
    rec = register_current_machine_as_trusted(
        developer_name=args.name,
        machine_alias=args.alias,
        roles=args.roles,
    )
    
    print("\n  🎉 THIS MACHINE HAS BEEN OFFICIALLY ADDED TO TRUSTED DEVELOPERS!")
    print(f"     Developer: {rec.developer_name}")
    print(f"     Alias:     {rec.machine_alias}")
    print(f"     Roles:     {', '.join(rec.authorized_roles)}")
    print(f"     Added At:  {rec.added_at}")
    print(f"     512-bit Signature: {rec.signature_512}")


if __name__ == "__main__":
    main()
