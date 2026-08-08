"""Blender-independent utility for detecting MTL files referenced by OBJ files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Regex: optional whitespace, "mtllib", whitespace, captured filename (rest of line).
_MTLLIB_RE = re.compile(r"^\s*mtllib\s+(.+)$", re.IGNORECASE)


@dataclass
class MTLDetectionResult:
    """Result of searching for an MTL file referenced by an OBJ."""

    path: Path | None = None
    """Resolved absolute path to the MTL file, or None if not found."""

    status: str = "NOT_FOUND"
    """One of: FOUND, NOT_FOUND, AMBIGUOUS, ERROR."""

    message: str = ""
    """Human-readable description of the detection outcome."""

    candidates: list[Path] = field(default_factory=list)
    """All MTL files considered, for AMBIGUOUS cases."""


def _read_obj_lines(obj_path: Path) -> list[str] | None:
    """Read an OBJ file as text, returning lines or None on failure.

    Tries UTF-8 first, falls back to latin-1 (which never fails for byte data).
    """
    try:
        with obj_path.open("r", encoding="utf-8") as fh:
            return fh.readlines()
    except UnicodeDecodeError:
        try:
            with obj_path.open("r", encoding="latin-1") as fh:
                return fh.readlines()
        except OSError:
            return None
    except OSError:
        return None


def _extract_mtllib_name(lines: list[str]) -> str | None:
    """Return the filename from the first meaningful mtllib declaration."""
    for line in lines:
        match = _MTLLIB_RE.match(line)
        if match:
            filename = match.group(1).strip()
            if filename:
                return filename
    return None


def _normalise_path(raw: str) -> str:
    """Normalise backslashes to forward slashes for cross-platform use."""
    return raw.replace("\\", "/")


def find_mtl_for_obj(obj_path: Path) -> MTLDetectionResult:
    """Detect the MTL material library referenced by an OBJ file.

    Steps:
    1. Parse the OBJ for an ``mtllib`` declaration.
    2. Resolve the referenced path relative to the OBJ directory.
    3. If not found, try a same-stem ``.mtl`` in the same directory.
    4. If still not found, look for a single ``.mtl`` file in the directory.
    5. Report ambiguous cases when multiple ``.mtl`` files exist.

    Args:
        obj_path: Absolute path to the OBJ file.

    Returns:
        A :class:`MTLDetectionResult` with ``path``, ``status``, and ``message``.
    """
    obj_dir = obj_path.parent

    # --- Read the OBJ file ---
    lines = _read_obj_lines(obj_path)
    if lines is None:
        return MTLDetectionResult(
            status="ERROR",
            message=f"Could not read OBJ file: {obj_path}",
        )

    # --- Extract mtllib reference ---
    mtl_name = _extract_mtllib_name(lines)

    # --- Resolve the referenced MTL ---
    if mtl_name:
        normalised = _normalise_path(mtl_name)
        candidate = (obj_dir / normalised).resolve()
        if candidate.is_file():
            return MTLDetectionResult(
                path=candidate,
                status="FOUND",
                message=f"MTL file found via mtllib: {candidate.name}",
            )
        # mtllib was declared but file does not exist — fall through to fallbacks.

    # --- Fallback 1: same stem as OBJ ---
    same_stem = obj_dir / f"{obj_path.stem}.mtl"
    if same_stem.is_file():
        return MTLDetectionResult(
            path=same_stem,
            status="FOUND",
            message=f"MTL file found via same-stem fallback: {same_stem.name}",
        )

    # --- Fallback 2: exactly one .mtl in the directory ---
    try:
        mtl_files = sorted(obj_dir.glob("*.mtl"))
    except OSError:
        mtl_files = []

    if len(mtl_files) == 1:
        return MTLDetectionResult(
            path=mtl_files[0],
            status="FOUND",
            message=(
                f"MTL file found via directory fallback: {mtl_files[0].name}"
            ),
        )

    if len(mtl_files) > 1:
        return MTLDetectionResult(
            status="AMBIGUOUS",
            message=(
                f"Multiple .mtl files found ({len(mtl_files)}). "
                "Cannot determine which one to use."
            ),
            candidates=mtl_files,
        )

    # --- Not found ---
    reason = (
        "No mtllib declaration in OBJ" if not mtl_name
        else f"Referenced MTL not found: {mtl_name}"
    )
    return MTLDetectionResult(
        status="NOT_FOUND",
        message=f"{reason}. No fallback MTL available.",
    )