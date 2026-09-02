"""
scripts/approve_changes.py — UniPlag & ICG Change Consensus & Approval CLI
Inspects pending code/heuristic changes, displays diff summary, and signs a new 512-bit
cryptographic block into the audit ledger using the local machine Sovereign Key.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.consensus import (
    inspect_pending_changes,
    approve_and_seal_changes,
    read_audit_ledger,
    verify_audit_ledger,
)
from app.integrity import get_sovereign_key_info


def main():
    parser = argparse.ArgumentParser(description="UniPlag 512-bit Change Consensus & Approval Tool")
    parser.add_argument("--author", "-a", default="Vlad & Aris", help="Author(s) of the changes")
    parser.add_argument("--message", "-m", default="Approved code updates", help="Description of approved changes")
    parser.add_argument("--status", action="store_true", help="Show current change delta and key status only")
    args = parser.parse_args()

    key_info = get_sovereign_key_info()
    delta = inspect_pending_changes()
    
    print("\n════════════════════════════════════════════════════════════")
    print("  🛡️  UniPlag Sovereign 512-bit Change Consensus Subsystem")
    print("════════════════════════════════════════════════════════════")
    print(f"  🔑 Key Size:        {key_info['key_size_bits']} bits (HMAC-SHA512)")
    print(f"  📁 Key Storage:     {key_info['key_storage']} (Git-Ignored: ✅)")
    print(f"  🏷️  Key Fingerprint: {key_info['key_fingerprint']}")
    print(f"  📦 Protected Files: {delta.current_file_count} (Signed: {delta.signed_file_count})")
    
    if delta.has_changes:
        print("\n  ⚠️  PENDING UNAPPROVED CHANGES DETECTED:")
        if delta.modified_files:
            print(f"    📝 Modified ({len(delta.modified_files)}):")
            for p in delta.modified_files:
                print(f"       ~ {p}")
        if delta.added_files:
            print(f"    ➕ Added ({len(delta.added_files)}):")
            for p in delta.added_files:
                print(f"       + {p}")
        if delta.removed_files:
            print(f"    ➖ Removed ({len(delta.removed_files)}):")
            for p in delta.removed_files:
                print(f"       - {p}")
    else:
        print("\n  🟢 All files in workspace are in full consensus with 512-bit signature.")

    # Show ledger summary
    blocks = read_audit_ledger()
    ledger_ok, ledger_msg = verify_audit_ledger()
    print(f"\n  📜 Cryptographic Audit Ledger: {len(blocks)} blocks recorded ({'VALID ✅' if ledger_ok else 'CORRUPT ❌'})")

    if args.status:
        return

    if not delta.has_changes and blocks:
        print("\n  ℹ️ No new changes to approve. Workspace is already clean and sealed.")
        return

    print(f"\n  ✍️  Approving and sealing changes with Sovereign 512-bit Key...")
    block = approve_and_seal_changes(author=args.author, description=args.message)
    print(f"  🎉 Block #{block.block_index} Successfully Signed & Recorded!")
    print(f"     Author:      {block.author}")
    print(f"     Description: {block.description}")
    print(f"     Block Hash:  {block.block_hash[:32]}... (SHA-512)")
    print(f"     Signature:   {block.manifest_signature[:32]}... (HMAC-SHA512)")


if __name__ == "__main__":
    main()
