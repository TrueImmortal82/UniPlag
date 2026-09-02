"""
scripts/build_blackbox.py — UniPlag Enterprise BlackBox Builder
==============================================================
Compiles Python sources to optimized bytecode (.pyc, O2), strips metadata,
packages HTML templates and assets into an in-memory archive, and encrypts
into a single-file distribution container: dist/UniPlag_Enterprise.bbx.
"""

from __future__ import annotations

import io
import os
import sys
import py_compile
import zipfile
import shutil
import hashlib
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.blackbox.crypto import encrypt_container, MAGIC_HEADER
from app.integrity import get_sovereign_key_512

DIST_DIR = PROJECT_ROOT / "dist"
OUTPUT_BBX = DIST_DIR / "UniPlag_Enterprise.bbx"
SCRATCH_BUILD = PROJECT_ROOT / "scratch" / "_bbx_build"


def compile_and_package_payload() -> bytes:
    """Compiles all application code to bytecode and bundles templates & assets into a zip byte stream."""
    if SCRATCH_BUILD.exists():
        shutil.rmtree(SCRATCH_BUILD)
    SCRATCH_BUILD.mkdir(parents=True, exist_ok=True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Compile and add app/ python modules as .pyc
        app_dir = PROJECT_ROOT / "app"
        for py_path in app_dir.rglob("*.py"):
            rel = py_path.relative_to(PROJECT_ROOT)
            pyc_target = SCRATCH_BUILD / f"{rel.with_suffix('.pyc')}"
            pyc_target.parent.mkdir(parents=True, exist_ok=True)

            # Compile with optimize=2 (removes docstrings & asserts for maximum anti-decompilation)
            py_compile.compile(str(py_path), cfile=str(pyc_target), optimize=2)
            
            zf.write(pyc_target, arcname=str(rel.with_suffix('.pyc')).replace("\\", "/"))

        # 2. Add templates
        templates_dir = app_dir / "templates"
        for tmpl in templates_dir.rglob("*.html"):
            rel = tmpl.relative_to(PROJECT_ROOT)
            zf.write(tmpl, arcname=str(rel).replace("\\", "/"))

        # 3. Add static files
        static_dirs = [app_dir / "static", PROJECT_ROOT / "static"]
        for sdir in static_dirs:
            if sdir.exists():
                for st in sdir.rglob("*"):
                    if st.is_file():
                        rel = st.relative_to(sdir)
                        zf.write(st, arcname=f"static/{rel}".replace("\\", "/"))
                        zf.write(st, arcname=f"app/static/{rel}".replace("\\", "/"))

        # 4. Add User Guide
        guide_file = PROJECT_ROOT / "USER_GUIDE.md"
        if guide_file.exists():
            zf.write(guide_file, arcname="USER_GUIDE.md")

    # Clean up scratch
    if SCRATCH_BUILD.exists():
        shutil.rmtree(SCRATCH_BUILD)

    return zip_buffer.getvalue()


def build_blackbox_distribution():
    print("\n" + "═" * 70)
    print("  🛡️  UNIPLAG & ICG — ENTERPRISE BLACKBOX BUILDER")
    print("═" * 70)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Gather & Compile Payload
    print("[1/3] ⚙️  Compiling sources into optimized O2 bytecode (.pyc) & assets...")
    payload_bytes = compile_and_package_payload()
    print(f"      Payload packed: {len(payload_bytes) / 1024:.1f} KB in RAM.")

    # 2. Encrypt with 512-bit Sovereign Key & AES-256-GCM
    print("[2/3] 🔒 Encrypting with AES-256-GCM & Sovereign HMAC-SHA512 seal...")
    master_key = get_sovereign_key_512()
    encrypted_bbx = encrypt_container(payload_bytes, master_key)
    print(f"      Encrypted container size: {len(encrypted_bbx) / 1024:.1f} KB.")

    # 3. Write .bbx distribution file
    print(f"[3/3] 📦 Writing standalone BlackBox container to: {OUTPUT_BBX.relative_to(PROJECT_ROOT)}")
    OUTPUT_BBX.write_bytes(encrypted_bbx)

    sha_hash = hashlib.sha512(encrypted_bbx).hexdigest()
    print("\n" + "═" * 70)
    print("  🎉 BLACKBOX BUILD COMPLETE!")
    print(f"  📁 Output File:       {OUTPUT_BBX.name}")
    print(f"  🏷️  Container Format:  UNIBBX v1 (AES-256-GCM + HMAC-SHA512)")
    print(f"  🔐 Container SHA-512: {sha_hash[:32]}...{sha_hash[-16:]}")
    print(f"  ⚡ In-Memory Boot:    READY for Zero-Disk Execution")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    build_blackbox_distribution()
