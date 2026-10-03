"""
run_blackbox.py — UniPlag Enterprise BlackBox Standalone In-Memory Launcher (v2)
===============================================================================
Zero-Disk Execution Engine:
  - Verifies the publisher Ed25519 digital signature on dist/UniPlag_Enterprise.bbx
    (attestation is asymmetric and does NOT require any secret).
  - Decrypts the v2 container directly into RAM (AES-256-GCM).
    Confidentiality: the per-build data key is wrapped to the Sovereign master
    secret (env UNIPLAG_SOVEREIGN_KEY_512 or .security/sovereign_512.key).
    Fail-closed: there is NO embedded fallback secret in this launcher.
  - Mounts in-memory bytecode & virtual assets into sys.meta_path.
  - Launches UniPlag & ICG Web Server on http://127.0.0.1:7932 with auto-browser.
  - Zero application files written to disk.

Security model (honest):
  - Attestation = real digital signature (Ed25519). Anyone can verify it with
    the published PUBLIC key; only the publisher can create valid containers.
  - Confidentiality is NOT absolute: a machine that holds the master secret can
    always extract the plaintext in memory. Per-install hardening is available
    via --bind-machine (Windows DPAPI) which binds the data key to this machine.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
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

# ---------------------------------------------------------------------------
# Container v2 format constants
# ---------------------------------------------------------------------------
MAGIC_HEADER = b"UNIBBX01"
FORMAT_CURRENT = 2
SALT_SIZE = 16
NONCE_SIZE = 12
SIG_SIZE = 64  # Ed25519 signature
WRAPPED_DK_SIZE = 48  # 32-byte key + 16-byte GCM tag
HEADER_SIZE = len(MAGIC_HEADER) + 2 + SALT_SIZE + NONCE_SIZE + NONCE_SIZE + WRAPPED_DK_SIZE
PBKDF2_ITERATIONS = 100_000

# ---------------------------------------------------------------------------
# Publisher Ed25519 PUBLIC key — SAFE to publish. The PRIVATE key never leaves
# the publisher machine (.security/release_ed25519.key is Git-ignored).
# ---------------------------------------------------------------------------
RELEASE_PUBLIC_KEY_HEX = "8e4ae977a03f0e8dbcc233443f7e37e8722a135c6f36160038f196d731ab6c14"

# ---------------------------------------------------------------------------
# Fail-closed master secret acquisition (no embedded fallback!)
# ---------------------------------------------------------------------------
def get_master_secret() -> bytes:
    env_k = os.environ.get("UNIPLAG_SOVEREIGN_KEY_512")
    if env_k:
        return bytes.fromhex(env_k.strip())
    local_k = Path(__file__).resolve().parent / ".security" / "sovereign_512.key"
    if local_k.exists():
        return bytes.fromhex(local_k.read_text("utf-8").strip())
    raise RuntimeError(
        "Sovereign 512-bit key is unavailable (fail-closed). "
        "Provide UNIPLAG_SOVEREIGN_KEY_512 or .security/sovereign_512.key "
        "(provisioning/activation key, NOT embedded in the launcher)."
    )


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
# 2. Cryptographic Engine (Ed25519 attestation + AES-256-GCM)
# ---------------------------------------------------------------------------
def verify_signature(container_bytes: bytes) -> tuple:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        print("❌ Ошибка: Не установлена библиотека cryptography.")
        print("   Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)

    if len(container_bytes) < HEADER_SIZE + SIG_SIZE:
        return False, "Container file is invalid or corrupted."
    if not container_bytes.startswith(MAGIC_HEADER):
        return False, "Invalid magic header: not a valid UniPlag .bbx container."
    if container_bytes[8:10] != struct.pack(">H", FORMAT_CURRENT):
        return False, "Unsupported container format (expected v2, Ed25519-attested)."

    signed_portion = container_bytes[8:-SIG_SIZE]
    expected_sig = container_bytes[-SIG_SIZE:]
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(RELEASE_PUBLIC_KEY_HEX))
        public_key.verify(expected_sig, signed_portion)
    except InvalidSignature:
        return False, "Ed25519 publisher signature invalid — container is NOT authentic or has been modified!"
    return True, "Ed25519 publisher attestation verified (authentic UniPlag release)"


def _parse_v2(container_bytes: bytes) -> dict:
    if len(container_bytes) < HEADER_SIZE + SIG_SIZE:
        raise ValueError("Container file is invalid or corrupted.")
    if not container_bytes.startswith(MAGIC_HEADER):
        raise ValueError("Invalid magic header: not a valid UniPlag .bbx container.")
    if container_bytes[8:10] != struct.pack(">H", FORMAT_CURRENT):
        raise ValueError("Unsupported container format (expected v2, Ed25519-attested).")

    offset = len(MAGIC_HEADER) + 2
    wrap_salt = container_bytes[offset:offset + SALT_SIZE]
    offset += SALT_SIZE
    wrap_nonce = container_bytes[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE
    payload_nonce = container_bytes[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE
    wrapped_dk = container_bytes[offset:offset + WRAPPED_DK_SIZE]
    offset += WRAPPED_DK_SIZE
    ciphertext = container_bytes[offset:-SIG_SIZE]
    return {
        "wrap_salt": wrap_salt,
        "wrap_nonce": wrap_nonce,
        "payload_nonce": payload_nonce,
        "wrapped_dk": wrapped_dk,
        "ciphertext": ciphertext,
    }


def decrypt_bbx_container(container_bytes: bytes, master_key: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    ok, msg = verify_signature(container_bytes)
    if not ok:
        raise ValueError(f"Digital Signature Check Failed: {msg}")

    parts = _parse_v2(container_bytes)
    aad_header = MAGIC_HEADER + struct.pack(">H", FORMAT_CURRENT)

    kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=parts["wrap_salt"], iterations=PBKDF2_ITERATIONS)
    wrap_key = kdf.derive(master_key)
    data_key = AESGCM(wrap_key).decrypt(parts["wrap_nonce"], parts["wrapped_dk"], aad_header)

    aad_body = aad_header + parts["wrap_salt"] + parts["wrap_nonce"] + parts["payload_nonce"] + parts["wrapped_dk"]
    decrypted = AESGCM(data_key).decrypt(parts["payload_nonce"], parts["ciphertext"], aad_body)
    return decrypted


# ---------------------------------------------------------------------------
# 2b. Optional Windows DPAPI machine binding (per-install hardening)
# ---------------------------------------------------------------------------
def dpapi_protect(data: bytes) -> bytes:
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    blob_out = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    local_free = ctypes.windll.kernel32.LocalFree
    if not crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0x1, ctypes.byref(blob_out)):
        raise RuntimeError("CryptProtectData failed")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        if blob_out.pbData:
            local_free(blob_out.pbData)


def dpapi_unprotect(blob: bytes) -> bytes:
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    buf = ctypes.create_string_buffer(blob, len(blob))
    blob_in = DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    blob_out = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    local_free = ctypes.windll.kernel32.LocalFree
    if not crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0x1, ctypes.byref(blob_out)):
        raise RuntimeError("CryptUnprotectData failed (container bound to another machine/user)")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        if blob_out.pbData:
            local_free(blob_out.pbData)


def decrypt_body_with_dk(container_bytes: bytes, data_key: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    parts = _parse_v2(container_bytes)
    aad_header = MAGIC_HEADER + struct.pack(">H", FORMAT_CURRENT)
    aad_body = aad_header + parts["wrap_salt"] + parts["wrap_nonce"] + parts["payload_nonce"] + parts["wrapped_dk"]
    return AESGCM(data_key).decrypt(parts["payload_nonce"], parts["ciphertext"], aad_body)


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
    parser = argparse.ArgumentParser(description="UniPlag Enterprise BlackBox Standalone Launcher (v2)")
    parser.add_argument("--container", type=Path, default=None, help="Path to .bbx container")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7932, help="Port (default: 7932)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--bind-machine", action="store_true", help="Bind the container data key to this machine via Windows DPAPI after first open")
    parser.add_argument("--verify-only", action="store_true", help="Verify the publisher Ed25519 attestation and exit (no key required)")
    args = parser.parse_args()

    print("\n" + "═" * 70)
    print("  🛡️  UNIPLAG & ICG ENTERPRISE — BLACKBOX STANDALONE LAUNCHER v2")
    print("═" * 70)

    # 1. Anti-Debug Check
    if check_debugger():
        print("🛑 [SECURITY ERROR] Active debugger detected. Execution terminated.")
        sys.exit(101)
    print("  [1/5] 🛡️  Анти-отладочный контур: АКТИВЕН (процесс защищён)")

    # 2. Locate container
    root_dir = Path(__file__).resolve().parent
    container_file = args.container or (root_dir / "dist" / "UniPlag_Enterprise.bbx")
    if not container_file.exists():
        print(f"❌ [ОШИБКА] Зашифрованный контейнер не найден: {container_file}")
        sys.exit(1)

    print(f"  [2/5] 📦 Загрузка аттестованного контейнера: {container_file.name} ({container_file.stat().st_size / 1024:.1f} KB)")
    container_bytes = container_file.read_bytes()

    # 3. Verify Ed25519 publisher attestation (no secret required)
    ok, att_msg = verify_signature(container_bytes)
    print(f"  [3/5] 🔏 Проверка Ed25519-подписи паблишера...")
    if not ok:
        print(f"❌ [ATTESTATION FAILURE] {att_msg}")
        sys.exit(102)
    print(f"        ✅ {att_msg}")

    if args.verify_only:
        print("\n  ✅ Аттестация подлинности подтверждена. Запуск не выполнен (--verify-only).")
        sys.exit(0)

    # 4. Open & decrypt in RAM (fail-closed: master secret required, or machine bind)
    print("  [4/5] 🔐 Расшифровка AES-256-GCM в оперативную память (Zero-Disk Footprint)...")
    try:
        if args.bind_machine:
            bind_cache = container_file.with_suffix(container_file.suffix + ".bind")
            master_key = None
            try:
                master_key = get_master_secret()
            except RuntimeError as e:
                print(f"        ⚠️  {e}")
            if bind_cache.exists():
                with open(bind_cache, "rb") as f:
                    data_key = dpapi_unprotect(f.read())
                decrypted_zip = decrypt_body_with_dk(container_bytes, data_key)
                print(f"        ✅ Machine-bound unlock via DPAPI кэш ({bind_cache.name})")
            else:
                if master_key is None:
                    raise RuntimeError("No master key and no DPAPI bind cache available.")
                data_key = None
                # Prove DK from master, then persist DPAPI-bound cache
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                from cryptography.hazmat.primitives import hashes
                parts = _parse_v2(container_bytes)
                aad_header = MAGIC_HEADER + struct.pack(">H", FORMAT_CURRENT)
                kdf = PBKDF2HMAC(algorithm=hashes.SHA512(), length=32, salt=parts["wrap_salt"], iterations=PBKDF2_ITERATIONS)
                wrap_key = kdf.derive(master_key)
                data_key = AESGCM(wrap_key).decrypt(parts["wrap_nonce"], parts["wrapped_dk"], aad_header)
                with open(bind_cache, "wb") as f:
                    f.write(dpapi_protect(data_key))
                decrypted_zip = decrypt_body_with_dk(container_bytes, data_key)
                print(f"        ✅ DPAPI-привязка к машине создана ({bind_cache.name})")
        else:
            master_key = get_master_secret()
            decrypted_zip = decrypt_bbx_container(container_bytes, master_key)
        print("        ✅ AES-256-GCM расшифровка и Ed25519-аттестация ПОДТВЕРЖДЕНЫ!")
    except Exception as e:
        print(f"❌ [ОШИБКА ЦЕЛОСТНОСТИ] Сбой расшифровки: {e}")
        sys.exit(102)

    # 5. Mount in-memory loader
    print("  [5/5] ⚡ Монтирование виртуального загрузчика sys.meta_path в RAM...")
    mount = mount_in_memory_container(decrypted_zip)
    print(f"        ✅ Смонтировано {len(mount.list_files())} виртуальных модулей и шаблонов.")

    # 6. Check Ollama
    check_and_prepare_ollama()

    # 7. Boot FastAPI Server
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
    print(f"  🚀 UNIPLAG & ICG ЗАПУЩЕН ИЗ АТТЕСТОВАННОГО BLACKBOX (v2)")
    print(f"  🌐 Адрес в браузере: {server_url}")
    print(f"  🔒 Режим:             Строго в ОЗУ (на диск ничего не сохраняется)")
    print("═" * 70 + "\n")

    if not args.no_browser:
        open_browser_delayed(server_url)

    uvicorn.run(app.main.app, host=args.host, port=active_port, log_level="info")


if __name__ == "__main__":
    main()