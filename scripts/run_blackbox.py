"""
scripts/run_blackbox.py — UniPlag Enterprise BlackBox Zero-Disk In-Memory Runner
================================================================================
Decryption and execution flow:
  1. Anti-Debugging & Environment Sanitization check.
  2. Cryptographic Integrity Validation of .bbx container (HMAC-SHA512).
  3. AES-256-GCM In-Memory Decryption (Zero files written to disk!).
  4. Virtual MetaPathFinder registration into sys.meta_path.
  5. In-Memory boot of FastAPI / Uvicorn server on http://127.0.0.1:7932.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.blackbox.antidebug import check_debugger_present
from app.blackbox.crypto import decrypt_container, verify_container_integrity
from app.blackbox.loader import mount_in_memory_container
from app.integrity import get_sovereign_key_512


def open_browser_delayed(url: str, delay: float = 1.2):
    def _target():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_target, daemon=True).start()


def run_blackbox_server(container_path: Optional[Path] = None, host: str = "127.0.0.1", port: int = 7932, no_browser: bool = False):
    print("\n" + "═" * 70)
    print("  🛡️  UNIPLAG & ICG — ENTERPRISE BLACKBOX RUNNER")
    print("═" * 70)

    # 1. Anti-Debug Shield Check
    is_debug, dbg_msg = check_debugger_present()
    if is_debug:
        print(f"🛑 [SECURITY ERROR] {dbg_msg}")
        sys.exit(101)
    print(f"  [1/4] 🛡️  Anti-Debugging Shield: ACTIVE ({dbg_msg})")

    # 2. Locate container file
    target_bbx = container_path or (PROJECT_ROOT / "dist" / "UniPlag_Enterprise.bbx")
    if not target_bbx.exists():
        print(f"❌ [ERROR] BlackBox container not found at: {target_bbx}")
        print("   Please build the container first: python scripts/build_blackbox.py")
        sys.exit(1)

    print(f"  [2/4] 📦 Loading encrypted container: {target_bbx.name} ({target_bbx.stat().st_size / 1024:.1f} KB)")
    container_bytes = target_bbx.read_bytes()

    # 3. Decrypt in memory
    master_key = get_sovereign_key_512()
    print("  [3/4] 🔐 Decrypting AES-256-GCM container into RAM (Zero-Disk Footprint)...")
    try:
        decrypted_zip = decrypt_container(container_bytes, master_key)
        print("        ✅ Decryption & 512-bit HMAC Signature VERIFIED!")
    except Exception as e:
        print(f"❌ [SECURITY INTEGRITY FAILURE] Decryption failed: {e}")
        sys.exit(102)

    # 4. Mount in-memory loader
    print("  [4/4] ⚡ Mounting Virtual MetaPathFinder into sys.meta_path...")
    mount = mount_in_memory_container(decrypted_zip)
    print(f"        ✅ Mounted {len(mount.list_files())} virtual files directly in memory.")

    # 5. Import and boot server
    import uvicorn
    import app.main
    from app.main import app as fastapi_app

    server_url = f"http://{host}:{port}"
    print("\n" + "═" * 70)
    print(f"  🚀 UNIPLAG & ICG SERVER RUNNING FROM ENCRYPTED BLACKBOX")
    print(f"  🌐 URL:  {server_url}")
    print(f"  🔒 Mode: Zero-Disk In-Memory Execution")
    print("═" * 70 + "\n")

    if not no_browser:
        open_browser_delayed(server_url)

    uvicorn.run(fastapi_app, host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="UniPlag Enterprise BlackBox Zero-Disk In-Memory Runner")
    parser.add_argument("--container", type=Path, default=None, help="Path to .bbx container file")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7932, help="Port (default: 7932)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    run_blackbox_server(container_path=args.container, host=args.host, port=args.port, no_browser=args.no_browser)


if __name__ == "__main__":
    main()
