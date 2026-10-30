import importlib


def test_home_data_directory_is_shared_by_settings_and_skill_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("IVYEA_OPS_DATA_DIR", "~/data/ivyeaops/runtime")
    from app.core import config, skill_paths

    try:
        importlib.reload(config)
        importlib.reload(skill_paths)
        expected = tmp_path / "data" / "ivyeaops" / "runtime"
        assert config.settings.data_dir == expected
        assert skill_paths.SKILLS_ROOT == (expected / "skills").resolve()
    finally:
        monkeypatch.undo()
        importlib.reload(config)
        importlib.reload(skill_paths)
