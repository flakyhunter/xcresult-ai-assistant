"""File system utilities."""

from __future__ import annotations

from pathlib import Path


def is_xcresult_bundle(path: Path) -> bool:
    """Check if path is an xcresult bundle."""
    return path.is_dir() and path.suffix == ".xcresult"


def is_supported_file(path: Path) -> bool:
    """Check if path is a supported input file."""
    if path.is_dir():
        return is_xcresult_bundle(path)

    supported_extensions = {".txt", ".log", ".xml"}
    return path.is_file() and path.suffix.lower() in supported_extensions


def find_xcresult_bundles(
    directory: Path,
    recursive: bool = True,
) -> list[Path]:
    """Find all xcresult bundles in a directory."""
    bundles = []

    if recursive:
        for path in directory.rglob("*.xcresult"):
            if path.is_dir():
                bundles.append(path)
    else:
        for path in directory.glob("*.xcresult"):
            if path.is_dir():
                bundles.append(path)

    return sorted(bundles)


def find_log_files(
    directory: Path,
    recursive: bool = True,
    extensions: set[str] | None = None,
) -> list[Path]:
    """Find all log/test result files in a directory."""
    if extensions is None:
        extensions = {".txt", ".log", ".xml"}

    files = []
    glob_func = directory.rglob if recursive else directory.glob

    for ext in extensions:
        for path in glob_func(f"*{ext}"):
            if path.is_file():
                files.append(path)

    return sorted(files)


def get_latest_xcresult(directory: Path) -> Path | None:
    """Get the most recently modified xcresult bundle."""
    bundles = find_xcresult_bundles(directory)
    if not bundles:
        return None

    return max(bundles, key=lambda p: p.stat().st_mtime)


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_read_text(path: Path, encoding: str = "utf-8") -> str:
    """Safely read text file with error handling."""
    try:
        return path.read_text(encoding=encoding, errors="replace")
    except Exception:
        return ""
