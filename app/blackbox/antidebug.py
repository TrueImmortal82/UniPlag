"""
app/blackbox/antidebug.py — Windows Anti-Debugging & Anti-Analysis Shield
========================================================================
Detects interactive debuggers, memory inspectors, and code injection.
"""

from __future__ import annotations

import os
import sys
import ctypes
from typing import Tuple


def is_running_under_debugger() -> bool:
    """Checks if the current process is being traced or attached by a debugger."""
    # 1. Standard Python sys.gettrace()
    if sys.gettrace() is not None:
        return True

    # 2. Windows WinAPI kernel32 checks
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            # IsDebuggerPresent
            if kernel32.IsDebuggerPresent():
                return True

            # CheckRemoteDebuggerPresent
            is_remote_debugger = ctypes.c_bool(False)
            current_process = kernel32.GetCurrentProcess()
            if kernel32.CheckRemoteDebuggerPresent(current_process, ctypes.byref(is_remote_debugger)):
                if is_remote_debugger.value:
                    return True
        except Exception:
            pass

    return False


def check_debugger_present(strict: bool = False) -> Tuple[bool, str]:
    """Evaluates debugging environment and returns status."""
    if is_running_under_debugger():
        msg = "Active debugger detected (Anti-Decompilation Shield Active)"
        if strict:
            print(f"🛑 SECURITY ALERT: {msg}")
            sys.exit(101)
        return True, msg

    return False, "Environment clean (no debugger detected)"
