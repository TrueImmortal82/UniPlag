"""
UniPlag & ICG Sovereign Server Launcher (run_server.py)
=======================================================
Production server launcher with advanced dual-tier rotating file logging:
  - logs/server.log: Full operational audit trail (Uvicorn requests, ICG passes, watchdog)
  - logs/error.log:  Isolated exception traces & critical errors
  - Console:         Colorized real-time status output

Includes:
  - Automatic pre-flight directory setup
  - 512-bit code integrity & trusted developer node verification
  - Port availability check & graceful collision handling
  - Crash-safe execution hook (prevents console window from vanishing on errors)
  - Optional browser auto-launch
"""

from __future__ import annotations

import argparse
import io
import logging
import logging.handlers
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

# Force UTF-8 encoding on Windows console to prevent cp1251/cp866 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Paths
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"
SECURITY_DIR = BASE_DIR / ".security"
SERVER_LOG_FILE = LOGS_DIR / "server.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures structured, rotated file and console logging."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    SECURITY_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.handlers.clear()

    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Operational Server Log (10 MB per file, 5 backup copies)
    server_file_handler = logging.handlers.RotatingFileHandler(
        SERVER_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    server_file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    server_file_handler.setFormatter(log_formatter)
    root_logger.addHandler(server_file_handler)

    # 2. Dedicated Error Log (10 MB per file, 5 backup copies)
    error_file_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(log_formatter)
    root_logger.addHandler(error_file_handler)

    # 3. Console Output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = logging.Formatter(
        f"{CYAN}%(asctime)s{RESET} [{BOLD}%(levelname)-7s{RESET}] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Forward uvicorn loggers to our rotating handlers
    for uvicorn_log in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_log)
        u_logger.handlers = root_logger.handlers
        u_logger.propagate = False

    logger = logging.getLogger("uniplag.server")
    logger.info("Logging initialized: server.log (INFO) and error.log (ERROR).")
    return logger


def is_port_available(host: str, port: int) -> bool:
    """Checks if a network port is open for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def crash_exception_handler(exc_type, exc_value, exc_traceback):
    """Logs uncaught exceptions to error.log and pauses before closing console window."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.getLogger("uniplag.server").critical(f"FATAL UNHANDLED EXCEPTION:\n{err_msg}")
    
    crash_banner = f"""
{RED}{BOLD}============================================================
  SERVER CRITICAL ERROR / EXCEPTION:
{err_msg}
  Details logged to: {ERROR_LOG_FILE}
============================================================{RESET}
"""
    safe_print(crash_banner)
    try:
        input("Press Enter to exit...")
    except Exception:
        pass


def open_browser_delayed(url: str, delay: float = 1.5):
    """Opens default web browser after a short delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        logging.getLogger("uniplag.server").warning(f"Could not auto-open browser: {e}")


def safe_print(text: str):
    """Prints text with automatic ASCII/fallback encoding if terminal codec fails."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            # Strip non-ASCII or non-cp1251
            safe_text = text.encode("ascii", errors="replace").decode("ascii")
            print(safe_text)
        except Exception:
            pass


def print_banner(host: str, port: int, key_bits: int, is_trusted: bool, dev_name: str):
    """Prints a clear startup banner with clickable links."""
    base_url = f"http://{host}:{port}" if host != "0.0.0.0" else f"http://localhost:{port}"
    banner_text = f"""
{CYAN}{BOLD}======================================================================
  UniPlag & ICG Sovereign Server v0.4.1
  Academic Plagiarism & Intellectual Contribution Analysis
======================================================================{RESET}
  {GREEN}*{RESET} {BOLD}Web Interface:{RESET}      {CYAN}{base_url}/{RESET}
  {GREEN}*{RESET} {BOLD}Login Page:{RESET}         {CYAN}{base_url}/login{RESET}
  {GREEN}*{RESET} {BOLD}Admin Panel:{RESET}        {CYAN}{base_url}/admin/users{RESET}
  {GREEN}*{RESET} {BOLD}512-bit Audit:{RESET}      {CYAN}{base_url}/admin/consensus{RESET}
  {GREEN}*{RESET} {BOLD}ICG Contour:{RESET}        {CYAN}{base_url}/admin/icg{RESET}

  {MAGENTA}*{RESET} {BOLD}Encryption:{RESET}         {key_bits}-bit HMAC-SHA512 (Local Master Key)
  {MAGENTA}*{RESET} {BOLD}Trusted Node:{RESET}       {dev_name} [{ 'TRUSTED / AUTHORIZED' if is_trusted else 'NOT REGISTERED' }]
  {MAGENTA}*{RESET} {BOLD}Logs Location:{RESET}      {SERVER_LOG_FILE}

  {YELLOW}Press Ctrl + C to stop server{RESET}
"""
    safe_print(banner_text)


def find_available_port(host: str, initial_port: int, max_attempts: int = 20) -> int:
    """Finds the first available port starting from initial_port."""
    for p in range(initial_port, initial_port + max_attempts):
        if is_port_available(host, p):
            return p
    return initial_port


def main():
    sys.excepthook = crash_exception_handler
    
    default_port = int(os.environ.get("UNIPLAG_PORT", "7932"))
    parser = argparse.ArgumentParser(description="UniPlag & ICG Server Launcher")
    parser.add_argument("--host", default="127.0.0.1", help="Binding host address (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=default_port, help="Binding port (default: 7932)")
    parser.add_argument("--strict-port", action="store_true", help="Fail if exact port is in use instead of auto-fallback")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    # 1. Initialize Logging System
    logger = setup_logging(debug=args.debug)
    
    # 2. Check Port Availability & Auto-fallback
    target_port = args.port
    if not is_port_available(args.host, target_port):
        if args.strict_port:
            logger.error(f"Port {target_port} is already in use by another process!")
            print(f"\n{RED}❌ Ошибка: Порт {target_port} уже занят другим приложением.{RESET}")
            print(f"Попробуйте запустить сервер на другом порту, например:")
            print(f"  {BOLD}python run_server.py --port 7933{RESET}\n")
            try:
                input("Нажмите Enter для выхода...")
            except Exception:
                pass
            sys.exit(1)
        else:
            free_port = find_available_port(args.host, target_port)
            if free_port != target_port:
                logger.warning(f"Port {target_port} is busy. Automatically switching to available port {free_port}.")
                print(f"\n{YELLOW}⚠️  Порт {target_port} занят другим процессом. Автоматически выбран свободный порт {free_port}.{RESET}\n")
                target_port = free_port

    logger.info(f"Starting UniPlag Server on {args.host}:{target_port}...")
    args.port = target_port

    # 3. Security Pre-flight Checks (512-bit & Trusted Developer)
    try:
        from app.integrity import get_sovereign_key_info, verify_code_integrity
        from app.trusted_nodes import is_current_machine_trusted
        
        key_info = get_sovereign_key_info()
        integrity = verify_code_integrity()
        is_trusted, dev_rec, _ = is_current_machine_trusted()
        dev_name = dev_rec.developer_name if dev_rec else "Неизвестный узел"

        logger.info(f"Sovereign Key: {key_info['key_size_bits']} bits (Fingerprint: {key_info['key_fingerprint']})")
        logger.info(f"Machine Trust: is_trusted={is_trusted}, dev='{dev_name}'")
        logger.info(f"Code Integrity: is_valid={integrity.is_valid}")
    except Exception as e:
        logger.warning(f"Security check exception during pre-flight: {e}")
        key_info = {"key_size_bits": 512}
        is_trusted = False
        dev_name = "Local Node"

    # 4. Print Banner
    print_banner(args.host, args.port, key_info.get("key_size_bits", 512), is_trusted, dev_name)

    # 5. Open Browser in background thread
    if not args.no_browser:
        target_url = f"http://localhost:{args.port}" if args.host in ("127.0.0.1", "0.0.0.0") else f"http://{args.host}:{args.port}"
        threading.Thread(target=open_browser_delayed, args=(target_url, 1.2), daemon=True).start()

    # 6. Run Uvicorn Server
    import uvicorn
    from app.main import app

    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_config=None,  # We manage logging via our custom handlers
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C).")
        print(f"\n{GREEN}Сервер успешно остановлен.{RESET}")
    except Exception as e:
        logger.critical(f"Server runtime failure: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
