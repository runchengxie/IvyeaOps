"""Source checkout uses src/; installed bundles retain client/ and server/."""
from pathlib import Path


def code_root(root: Path) -> Path:
    root=Path(root)
    source=root/'src'
    return source if (source/'server').is_dir() else root


def environment_file(root: Path) -> Path:
    current=code_root(root)/'server'/'.env'
    legacy=Path(root)/'server'/'.env'
    return legacy if not current.is_file() and legacy.is_file() else current
