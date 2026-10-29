"""Application version helpers."""
from __future__ import annotations

import subprocess
import logging
import sys
from pathlib import Path

logger = logging.getLogger("ivyea.core.version")


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[4]


_CACHED: str | None = None


def _git_tag(root: Path) -> str:
    """Latest tag reachable from HEAD on a git checkout, or '' if unavailable."""
    if not (root / ".git").exists():
        return ""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=3,
        )
        return (out.stdout or "").strip()
    except Exception:
        return ""


def app_version() -> str:
    """Reported version.

    Git checkouts prefer their latest tag. Source archives use docs/version.
    Frozen bundles use the root VERSION written by the release workflow.
    A legacy root VERSION remains a fallback for older source archives.

    Git checkout: **不缓存**——每次读 git tag。开发机在本机 commit+tag 发版后，运行中的
    服务下次检测就能反映最新 tag，无需重启（否则 _CACHED 停在启动时的旧版本，明明是最新代码
    却一直误报"有更新"变红）。git describe 很轻(~10ms)。frozen/VERSION 路径仍缓存。"""
    root = runtime_root()
    if not getattr(sys, "frozen", False):
        tag = _git_tag(root)
        if tag:
            return tag
    global _CACHED
    if _CACHED is not None:
        return _CACHED
    try:
        path = root / "VERSION" if getattr(sys, "frozen", False) else root / "docs" / "version"
        if not path.is_file():
            path = root / "VERSION"
        value = path.read_text(encoding="utf-8").strip()
        if value:
            _CACHED = value
            return value
    except Exception:
        logger.debug("value = 失败（旁路，已忽略）", exc_info=True)
    _CACHED = "dev"
    return _CACHED
