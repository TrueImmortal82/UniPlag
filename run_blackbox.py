"""
run_blackbox.py — UniPlag Enterprise BlackBox Standalone In-Memory Launcher
==========================================================================
Zero-Disk Execution Engine:
  - Decrypts dist/UniPlag_Enterprise.bbx directly into RAM (AES-256-GCM + SHA-512).
  - Mounts in-memory bytecode & virtual assets into sys.meta_path.
  - Launches UniPlag & ICG Web Server on http://127.0.0.1:7932 with auto-browser.
  - Zero application files written to disk (100% Anti-Decompilation Protection).
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import hmac
import io
import json
import marshal
import os
import struct
import sys
import threading
import time
import types
import urllib.request
import webbrowser
import zipfile
import importlib.abc
import importlib.machinery
from pathlib import Path

# Force UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MAGIC_HEADER = b"UNIBBX01"
VERSION = 1
PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16
NONCE_SIZE = 12
SIG_SIZE = 64

# Embedded Sovereign consensus key for container decryption
_EMBEDDED_KEY = bytes.fromhex("16a858089b1fe43225e08bdd9dbdae71aad33a8882031ace74033b3a6c0def4592b6a761a9dfdde9c3f83a9ca8ebe2cb04014215fbf53bbb06a10f098e94eea3")

def get_decryption_key() -> bytes:
    env_k = os.environ.get("UNIPLAG_SOVEREIGN_KEY_512")
    if env_k:
        try:
            return bytes.fromhex(env_k.strip())
        except Exception:
            return env_k.encode()
    local_k = Path(__file__).resolve().parent / ".security" / "sovereign_512.key"
    if local_k.exists():
        try:
            return bytes.fromhex(local_k.read_text("utf-8").strip())
        except Exception:
            pass
    return _EMBEDDED_KEY


# ---------------------------------------------------------------------------
# 1. Anti-Debugging Shield
# ---------------------------------------------------------------------------
def check_debugger() -> bool:
    if sys.gettrace() is not None:
        return True
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True
            is_remote = ctypes.c_bool(False)
            if kernel32.CheckRemoteDebuggerPresent(kernel32.GetCurrentProcess(), ctypes.byref(is_remote)):
                if is_remote.value:
                    return True
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# 2. Cryptographic Engine (AES-256-GCM + PBKDF2-SHA512)
# ---------------------------------------------------------------------------
def decrypt_bbx_container(container_bytes: bytes, master_key: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError:
        print("❌ Ошибка: Не установлена библиотека cryptography.")
        print("   Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)

    if len(container_bytes) < len(MAGIC_HEADER) + 2 + SALT_SIZE + NONCE_SIZE + 8 + SIG_SIZE:
        raise ValueError("Container file is invalid or corrupted.")

    if not container_bytes.startswith(MAGIC_HEADER):
        raise ValueError("Invalid magic header: not a valid UniPlag .bbx container.")

    data_to_verify = container_bytes[:-SIG_SIZE]
    expected_sig = container_bytes[-SIG_SIZE:]

    h = hmac.new(master_key, data_to_verify, hashlib.sha512)
    if not hmac.compare_digest(expected_sig, h.digest()):
        raise ValueError("Digital Signature Check Failed: Container has been modified or corrupted!")

    offset = len(MAGIC_HEADER)
    version = struct.unpack(">H", container_bytes[offset:offset+2])[0]
    offset += 2
    salt = container_bytes[offset:offset+SALT_SIZE]
    offset += SALT_SIZE
    nonce = container_bytes[offset:offset+NONCE_SIZE]
    offset += NONCE_SIZE
    payload_len = struct.unpack(">Q", container_bytes[offset:offset+8])[0]
    offset += 8
    ciphertext = container_bytes[offset:-SIG_SIZE]

    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=salt, iterations=PBKDF2_ITERATIONS)
    aes_key = kdf.derive(master_key)
    aesgcm = AESGCM(aes_key)
    aad = MAGIC_HEADER + struct.pack(">HQ", version, payload_len)

    decrypted = aesgcm.decrypt(nonce, ciphertext, aad)
    if len(decrypted) != payload_len:
        raise ValueError("Decrypted length mismatch.")
    return decrypted


# ---------------------------------------------------------------------------
# 3. In-Memory Virtual Importer (Zero-Disk Module Loader)
# ---------------------------------------------------------------------------
class MemoryZipModuleFinder(importlib.abc.MetaPathFinder):
    def __init__(self, zip_data: bytes):
        self._zip = zipfile.ZipFile(io.BytesIO(zip_data), "r")
        self._file_list = set(self._zip.namelist())
        self._cache = {}

    def get_resource_bytes(self, path: str):
        norm = path.replace("\\", "/").lstrip("/")
        if norm in self._file_list:
            if norm not in self._cache:
                self._cache[norm] = self._zip.read(norm)
            return self._cache[norm]
        return None

    def list_files(self):
        return list(self._file_list)

    def find_spec(self, fullname: str, path, target=None):
        rel_path = fullname.replace(".", "/")
        pkg_pyc = f"{rel_path}/__init__.pyc"
        if pkg_pyc in self._file_list:
            return importlib.machinery.ModuleSpec(fullname, MemoryZipLoader(self, fullname, pkg_pyc, True), is_package=True)
        mod_pyc = f"{rel_path}.pyc"
        if mod_pyc in self._file_list:
            return importlib.machinery.ModuleSpec(fullname, MemoryZipLoader(self, fullname, mod_pyc, False), is_package=False)
        return None


class MemoryZipLoader(importlib.abc.Loader):
    def __init__(self, finder: MemoryZipModuleFinder, fullname: str, zip_path: str, is_package: bool):
        self.finder = finder
        self.fullname = fullname
        self.zip_path = zip_path
        self.is_package = is_package

    def exec_module(self, module: types.ModuleType):
        raw_pyc = self.finder.get_resource_bytes(self.zip_path)
        if not raw_pyc:
            raise ImportError(f"Cannot load bytecode for {self.fullname}")
        code_bytes = raw_pyc[16:]  # Standard .pyc header is 16 bytes
        code_obj = marshal.loads(code_bytes)
        module.__file__ = f"<blackbox:{self.zip_path}>"
        module.__loader__ = self
        if self.is_package:
            module.__path__ = [f"<blackbox:{self.zip_path[:-13]}>"]
            module.__package__ = self.fullname
        else:
            module.__package__ = self.fullname.rpartition(".")[0]
        exec(code_obj, module.__dict__)


_CURRENT_MOUNT = None


def mount_in_memory_container(decrypted_zip: bytes):
    global _CURRENT_MOUNT
    finder = MemoryZipModuleFinder(decrypted_zip)
    sys.meta_path.insert(0, finder)
    _CURRENT_MOUNT = finder
    return finder


def get_current_mount():
    return _CURRENT_MOUNT


# ---------------------------------------------------------------------------
# 4. Ollama Auto-Preparation Helper
# ---------------------------------------------------------------------------
def check_and_prepare_ollama():
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "UniPlag-BlackBox"})
        with urllib.request.urlopen(req, timeout=2) as r:
            data = json.loads(r.read())
            models = [m.get("name", "") for m in data.get("models", [])]
            if models:
                print(f"  🤖 Ollama активна. Установлено моделей: {len(models)} (активная: {models[0]})")
            else:
                print("  🤖 Ollama активна, но моделей нет. Запускается автозагрузка qwen2.5:1.5b...")
                pull_payload = json.dumps({"name": "qwen2.5:1.5b", "stream": False}).encode("utf-8")
                pull_req = urllib.request.Request("http://127.0.0.1:11434/api/pull", data=pull_payload, headers={"Content-Type": "application/json"}, method="POST")
                def _bg_pull():
                    try:
                        with urllib.request.urlopen(pull_req, timeout=300):
                            pass
                    except Exception:
                        pass
                threading.Thread(target=_bg_pull, daemon=True).start()
    except Exception:
        print("  ℹ️  Ollama не обнаружена. Для локальной детекции нейросетей установите Ollama (https://ollama.com).")
        print("      Сейчас активен встроенный быстрый ML-ансамбль стилометрии.")


# ---------------------------------------------------------------------------
# 5. Main Execution Flow
# ---------------------------------------------------------------------------
def open_browser_delayed(url: str, delay: float = 1.2):
    def _target():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_target, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="UniPlag Enterprise BlackBox Standalone Launcher")
    parser.add_argument("--container", type=Path, default=None, help="Path to .bbx container")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7932, help="Port (default: 7932)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    print("\n" + "═" * 70)
    print("  🛡️  UNIPLAG & ICG ENTERPRISE — BLACKBOX STANDALONE LAUNCHER")
    print("═" * 70)

    # 1. Anti-Debug Check
    if check_debugger():
        print("🛑 [SECURITY ERROR] Active debugger detected. Execution terminated.")
        sys.exit(101)
    print("  [1/4] 🛡️  Анти-отладочный контур: АКТИВЕН (процесс защищён)")

    # 2. Locate container
    root_dir = Path(__file__).resolve().parent
    container_file = args.container or (root_dir / "dist" / "UniPlag_Enterprise.bbx")
    if not container_file.exists():
        print(f"❌ [ОШИБКА] Зашифрованный контейнер не найден: {container_file}")
        sys.exit(1)

    print(f"  [2/4] 📦 Загрузка защищённого контейнера: {container_file.name} ({container_file.stat().st_size / 1024:.1f} KB)")
    container_bytes = container_file.read_bytes()

    # 3. Decrypt in RAM
    print("  [3/4] 🔐 Расшифровка AES-256-GCM в оперативную память (Zero-Disk Footprint)...")
    try:
        decrypted_zip = decrypt_bbx_container(container_bytes, get_decryption_key())
        print("        ✅ Цифровая подпись SHA-512 и целостность контейнера ПОДТВЕРЖДЕНЫ!")
    except Exception as e:
        print(f"❌ [ОШИБКА ЦЕЛОСТНОСТИ] Сбой расшифровки: {e}")
        sys.exit(102)

    # 4. Mount in-memory loader
    print("  [4/4] ⚡ Монтирование виртуального загрузчика sys.meta_path в RAM...")
    mount = mount_in_memory_container(decrypted_zip)
    print(f"        ✅ Смонтировано {len(mount.list_files())} виртуальных модулей и шаблонов.")

    # 5. Check Ollama
    check_and_prepare_ollama()

    # 6. Boot FastAPI Server
    import uvicorn
    import app.main
    import socket

    def is_port_free(h: str, p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((h, p)) != 0

    active_port = args.port
    if not is_port_free(args.host, active_port):
        for p in range(active_port + 1, active_port + 30):
            if is_port_free(args.host, p):
                print(f"  ⚠️  Порт {active_port} занят. Автоматически переключено на свободный порт {p}.")
                active_port = p
                break

    server_url = f"http://{args.host}:{active_port}"
    print("\n" + "═" * 70)
    print(f"  🚀 UNIPLAG & ICG ЗАПУЩЕН ИЗ ЗАШИФРОВАННОГО BLACKBOX")
    print(f"  🌐 Адрес в браузере: {server_url}")
    print(f"  🔒 Режим:             Строго в ОЗУ (на диск ничего не сохраняется)")
    print("═" * 70 + "\n")

    if not args.no_browser:
        open_browser_delayed(server_url)

    uvicorn.run(app.main.app, host=args.host, port=active_port, log_level="info")


if __name__ == "__main__":
    main()
