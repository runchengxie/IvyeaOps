import os
import subprocess
import sys
from pathlib import Path


def test_home_data_directory_is_shared_by_settings_and_skill_paths(tmp_path):
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if key in os.environ}
    env.update(
        HOME=str(tmp_path),
        USERPROFILE=str(tmp_path),
        IVYEA_OPS_DATA_DIR="~/data/ivyeaops/runtime",
    )
    code = """
from pathlib import Path
from app.core.config import settings
from app.core.skill_paths import SKILLS_ROOT, STUDIO_ROOT
expected = Path.home() / 'data' / 'ivyeaops' / 'runtime'
assert settings.data_dir == expected
assert SKILLS_ROOT == (expected / 'skills').resolve()
assert STUDIO_ROOT == (expected / 'skill-studio').resolve()
"""
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
