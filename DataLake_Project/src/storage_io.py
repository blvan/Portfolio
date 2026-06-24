"""Thin storage abstraction to support local FS and Azure Data Lake (ADLS Gen2) via fsspec/adlfs.

Env variables for ADLS mode:
- ADLS_ACCOUNT: Storage account name
- ADLS_KEY:     Storage account key (or set ADLS_SAS for SAS token)
- ADLS_FILESYSTEM: Filesystem (container) name, e.g., datalake

When ADLS_* are provided, functions operate on abfs:// paths using fsspec.
Otherwise they operate on local filesystem under project root.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple, Iterable
import importlib


def _is_adls_enabled() -> bool:
    return bool(os.getenv("ADLS_ACCOUNT") and os.getenv("ADLS_FILESYSTEM") and (os.getenv("ADLS_KEY") or os.getenv("ADLS_SAS")))


def _get_adls_fs():
    """Return fsspec filesystem for ADLS, supporting key/SAS or Azure Identity (CLI/MI)."""
    fsspec = importlib.import_module("fsspec")

    storage_options = {"account_name": os.getenv("ADLS_ACCOUNT")}

    # Prefer key / SAS if provided
    if os.getenv("ADLS_KEY"):
        storage_options["account_key"] = os.getenv("ADLS_KEY")
    if os.getenv("ADLS_SAS"):
        storage_options["sas_token"] = os.getenv("ADLS_SAS")

    # If neither key nor SAS is present, try Azure Identity (CLI / Managed Identity)
    if not storage_options.get("account_key") and not storage_options.get("sas_token"):
        try:
            azure_identity = importlib.import_module("azure.identity")
            credential = azure_identity.DefaultAzureCredential()
            storage_options["credential"] = credential
        except Exception:
            pass

    return fsspec.filesystem("abfs", **storage_options)


def adls_prefix() -> str:
    """Return abfs://<filesystem> prefix when ADLS is enabled."""
    return f"abfs://{os.getenv('ADLS_FILESYSTEM')}"


def ensure_dir(path: str | Path) -> None:
    if _is_adls_enabled():
        fs = _get_adls_fs()
        fs.makedirs(str(path), exist_ok=True)
    else:
        Path(path).mkdir(parents=True, exist_ok=True)


def open_file(path: str | Path, mode: str, encoding: Optional[str] = None):
    if _is_adls_enabled():
        fs = _get_adls_fs()
        return fs.open(str(path), mode, encoding=encoding)
    else:
        return open(Path(path), mode, encoding=encoding)


def glob(pattern: str | Path) -> Iterable[str]:
    if _is_adls_enabled():
        fs = _get_adls_fs()
        return fs.glob(str(pattern))
    else:
        from glob import glob as _glob
        return _glob(str(pattern))


def join(*parts: str | Path) -> str:
    # For ADLS we join with '/', for local use Path
    if _is_adls_enabled():
        # Handle abfs:// prefix specially to preserve double slash
        parts_str = [str(p) for p in parts]
        if parts_str and parts_str[0].startswith("abfs://"):
            prefix = parts_str[0]  # "abfs://datalake"
            rest = [p.strip("/") for p in parts_str[1:] if p]
            return prefix + "/" + "/".join(rest) if rest else prefix
        else:
            return "/".join(str(p).strip("/") for p in parts if p)
    else:
        return str(Path(*[str(p) for p in parts]))


def is_adls_enabled() -> bool:
    return _is_adls_enabled()


def exists(path: str | Path) -> bool:
    if _is_adls_enabled():
        fs = _get_adls_fs()
        try:
            return fs.exists(str(path))
        except Exception:
            return False
    else:
        return Path(path).exists()
