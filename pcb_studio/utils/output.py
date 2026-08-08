"""Output path validation and construction utility."""

from __future__ import annotations

from pathlib import Path


def validate_output_path(directory: str, filename: str) -> Path:
    """Construct and validate an output file path.

    Appends ``.png`` if the filename lacks it.  Raises ``ValueError``
    for empty or invalid paths.

    Args:
        directory: Output directory path.
        filename: Output filename (with or without extension).

    Returns:
        Resolved absolute ``Path``.

    Raises:
        ValueError: If *directory* is empty or does not exist, or
            *filename* is empty after stripping.
    """
    stripped = filename.strip()
    if not stripped:
        raise ValueError("Filename must not be empty.")

    if not directory or not directory.strip():
        raise ValueError("Output directory must not be empty.")

    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        raise ValueError(f"Output directory does not exist: {dir_path}")

    path = dir_path / stripped
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")

    return path.resolve()