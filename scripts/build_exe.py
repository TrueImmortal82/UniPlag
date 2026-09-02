"""
scripts/build_exe.py — UniPlag & ICG Standalone Server PyInstaller Builder
Compiles run_server.py into UniPlag_Server.exe bundling templates, static assets,
reference benchmark files, and machine learning runtime dependencies.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ENTRY_POINT = PROJECT_ROOT / "run_server.py"

def build():
    print("\n════════════════════════════════════════════════════════════")
    print("  🔨  Building UniPlag_Server.exe via PyInstaller")
    print("════════════════════════════════════════════════════════════\n")

    # Command arguments for PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=UniPlag_Server",
        "--onedir",
        "--clean",
        "--noconfirm",
        # Include data directories
        "--add-data=app/templates;app/templates",
        "--add-data=app/static;app/static",
        "--add-data=app/icg/benchmarks/reference;app/icg/benchmarks/reference",
        # Hidden imports
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespans",
        "--hidden-import=uvicorn.lifespans.on",
        "--hidden-import=sentence_transformers",
        "--hidden-import=sklearn",
        "--hidden-import=jinja2",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        str(ENTRY_POINT),
    ]

    print("Running build command:", " ".join(cmd[:8]), "...")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode == 0:
        exe_path = DIST_DIR / "UniPlag_Server" / "UniPlag_Server.exe"
        print("\n════════════════════════════════════════════════════════════")
        print(f"  🎉 BUILD SUCCESSFUL!")
        print(f"  📁 Output Directory: {DIST_DIR / 'UniPlag_Server'}")
        print(f"  ⚡ Executable:       {exe_path}")
        print("════════════════════════════════════════════════════════════\n")
    else:
        print(f"\n❌ Build failed with exit code: {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
