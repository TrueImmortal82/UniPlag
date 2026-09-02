"""
app/blackbox/loader.py — Zero-Disk In-Memory Module & Asset Loader
==================================================================
Mounts and imports compiled bytecode (.pyc), templates, and static assets
directly from an in-memory decrypted archive into sys.meta_path without
ever touching the filesystem.
"""

from __future__ import annotations

import io
import sys
import marshal
import types
import zipfile
import importlib.abc
import importlib.machinery
from typing import Dict, Any, Optional, List, Tuple


class MemoryZipModuleFinder(importlib.abc.MetaPathFinder):
    """Custom MetaPathFinder that finds and loads compiled bytecode from an in-memory ZipFile."""

    def __init__(self, zip_data: bytes):
        self._zip_bytes = zip_data
        self._zip = zipfile.ZipFile(io.BytesIO(zip_data), "r")
        self._file_list = set(self._zip.namelist())
        self._cache: Dict[str, bytes] = {}

    def get_resource_bytes(self, path: str) -> Optional[bytes]:
        """Retrieves raw asset bytes (templates, static files, data) from memory."""
        normalized = path.replace("\\", "/").lstrip("/")
        if normalized in self._file_list:
            if normalized not in self._cache:
                self._cache[normalized] = self._zip.read(normalized)
            return self._cache[normalized]
        return None

    def list_files(self) -> List[str]:
        return list(self._file_list)

    def find_spec(self, fullname: str, path: Optional[List[str]], target: Optional[types.ModuleType] = None):
        rel_path = fullname.replace(".", "/")
        
        # 1. Check if package (__init__.pyc)
        pkg_pyc = f"{rel_path}/__init__.pyc"
        if pkg_pyc in self._file_list:
            loader = MemoryZipLoader(self, fullname, pkg_pyc, is_package=True)
            return importlib.machinery.ModuleSpec(fullname, loader, is_package=True)

        # 2. Check if module (.pyc)
        mod_pyc = f"{rel_path}.pyc"
        if mod_pyc in self._file_list:
            loader = MemoryZipLoader(self, fullname, mod_pyc, is_package=False)
            return importlib.machinery.ModuleSpec(fullname, loader, is_package=False)

        return None


class MemoryZipLoader(importlib.abc.Loader):
    """Custom Loader that executes unmarshalled PyCodeObject directly in RAM."""

    def __init__(self, finder: MemoryZipModuleFinder, fullname: str, zip_path: str, is_package: bool):
        self.finder = finder
        self.fullname = fullname
        self.zip_path = zip_path
        self.is_package = is_package

    def create_module(self, spec):
        return None  # Use default module creation

    def exec_module(self, module: types.ModuleType):
        raw_pyc = self.finder.get_resource_bytes(self.zip_path)
        if not raw_pyc:
            raise ImportError(f"Cannot load in-memory bytecode for {self.fullname}")

        # Standard .pyc header in Python 3.7+ is 16 bytes (Magic, flags, timestamp/hash, size)
        header_size = 16
        code_bytes = raw_pyc[header_size:]
        code_obj = marshal.loads(code_bytes)

        module.__file__ = f"<blackbox:{self.zip_path}>"
        module.__loader__ = self
        if self.is_package:
            module.__path__ = [f"<blackbox:{self.zip_path[:-13]}>"]
            module.__package__ = self.fullname
        else:
            module.__package__ = self.fullname.rpartition(".")[0]

        exec(code_obj, module.__dict__)


_CURRENT_MOUNT: Optional[MemoryZipModuleFinder] = None


def mount_in_memory_container(decrypted_zip_bytes: bytes) -> MemoryZipModuleFinder:
    """Installs the in-memory loader into sys.meta_path and returns the finder instance."""
    global _CURRENT_MOUNT
    finder = MemoryZipModuleFinder(decrypted_zip_bytes)
    sys.meta_path.insert(0, finder)
    _CURRENT_MOUNT = finder
    return finder


def get_current_mount() -> Optional[MemoryZipModuleFinder]:
    return _CURRENT_MOUNT
