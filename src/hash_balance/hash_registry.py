"""Load and validate user-specified hash functions."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


HashFn = Callable[[bytes], int]


@dataclass
class HashTarget:
    """A named hash function referenced by an import path."""

    name: str
    path: str
    enabled: bool = True


DEFAULT_HASH_TARGETS: list[HashTarget] = [
    HashTarget("flawed_hash", "hash_balance.flawed_hash:flawed_hash"),
    HashTarget("reference_hash", "hash_balance.flawed_hash:reference_hash"),
]


class HashResolutionError(ValueError):
    """Raised when a hash import path cannot be resolved or validated."""


def _split_path(path: str) -> tuple[str, str]:
    """Split a path into module/file and attribute parts."""
    if ":" in path:
        module_part, attr = path.rsplit(":", 1)
    else:
        module_part, attr = path.rsplit(".", 1)

    module_part = module_part.strip()
    attr = attr.strip()
    if not module_part or not attr:
        raise HashResolutionError(
            f"Invalid hash path {path!r}. "
            "Use module:function, module.function, or path/to/file.py:function"
        )
    return module_part, attr


def _load_module(module_part: str, attr: str):
    """Import a module from a package path or a .py file path."""
    path = Path(module_part)
    if module_part.endswith(".py") or path.is_file():
        file_path = path.resolve()
        if not file_path.is_file():
            raise HashResolutionError(f"Hash file not found: {module_part}")

        module_name = f"hash_balance.user.{file_path.stem}_{attr}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise HashResolutionError(f"Could not load hash file: {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    try:
        return importlib.import_module(module_part)
    except ModuleNotFoundError as exc:
        raise HashResolutionError(f"Module not found: {module_part}") from exc


def _validate_hash_fn(fn: object) -> HashFn:
    """Ensure the callable accepts bytes and returns an integer bucket value."""
    if not callable(fn):
        raise HashResolutionError("Hash path must point to a callable")

    try:
        result = fn(b"\x00")
    except Exception as exc:
        raise HashResolutionError(f"Hash call failed for test input: {exc}") from exc

    if not isinstance(result, int):
        raise HashResolutionError("Hash must return an int")

    return fn  # type: ignore[return-value]


def resolve_hash(path: str) -> HashFn:
    """Resolve an import path to a validated bytes -> int hash function."""
    module_part, attr = _split_path(path)
    module = _load_module(module_part, attr)

    try:
        fn = getattr(module, attr)
    except AttributeError as exc:
        raise HashResolutionError(
            f"Attribute {attr!r} not found in {module_part!r}"
        ) from exc

    return _validate_hash_fn(fn)


def resolve_targets(targets: list[HashTarget]) -> list[tuple[str, HashFn]]:
    """Resolve all enabled hash targets, raising on the first failure."""
    resolved: list[tuple[str, HashFn]] = []
    for target in targets:
        if not target.enabled:
            continue
        resolved.append((target.name, resolve_hash(target.path)))
    return resolved
