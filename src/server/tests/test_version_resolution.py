"""app_version() prefers the git tag on a checkout, so a stale VERSION file
never makes a freshly-pulled server think it is behind."""
from __future__ import annotations

import app.core.version as v


def test_prefers_git_tag_over_version_file(monkeypatch):
    v._CACHED = None
    monkeypatch.setattr(v, "_git_tag", lambda root: "v9.9.9")
    assert v.app_version() == "v9.9.9"


def test_falls_back_to_version_file_without_git(monkeypatch, tmp_path):
    v._CACHED = None
    (tmp_path / "VERSION").write_text("v1.2.3", encoding="utf-8")
    monkeypatch.setattr(v, "runtime_root", lambda: tmp_path)
    monkeypatch.setattr(v, "_git_tag", lambda root: "")
    assert v.app_version() == "v1.2.3"


def test_dev_when_nothing_available(monkeypatch, tmp_path):
    v._CACHED = None
    monkeypatch.setattr(v, "runtime_root", lambda: tmp_path)
    monkeypatch.setattr(v, "_git_tag", lambda root: "")
    assert v.app_version() == "dev"


def test_source_version_uses_docs_version_when_git_tag_unavailable(monkeypatch, tmp_path):
    v._CACHED = None
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version").write_text("v2.3.4", encoding="utf-8")
    monkeypatch.setattr(v, "runtime_root", lambda: tmp_path)
    monkeypatch.setattr(v, "_git_tag", lambda root: "")
    monkeypatch.setattr(v.sys, "frozen", False, raising=False)
    assert v.app_version() == "v2.3.4"


def test_frozen_bundle_prefers_its_root_version(monkeypatch, tmp_path):
    v._CACHED = None
    (tmp_path / "VERSION").write_text("v3.0.0", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version").write_text("v2.0.0", encoding="utf-8")
    monkeypatch.setattr(v, "runtime_root", lambda: tmp_path)
    monkeypatch.setattr(v.sys, "frozen", True, raising=False)
    assert v.app_version() == "v3.0.0"
