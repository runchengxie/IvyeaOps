"""Regression for hosts whose MIME registry incorrectly maps JS to text/plain."""
import os
from pathlib import Path
import subprocess
import sys


def test_javascript_assets_override_host_mime_registry(tmp_path):
    assets = tmp_path / 'client' / 'dist' / 'assets'
    assets.mkdir(parents=True)
    for suffix in ('js', 'mjs'):
        (assets / f'module.{suffix}').write_text('export const ok = true;', encoding='utf-8')
    # main constructs its routes on import. Keep its temporary root and the
    # simulated host registry out of the parent test process entirely.
    script = '''
import mimetypes
import sys
from pathlib import Path
from app.core.config import settings
settings.root_dir = Path(sys.argv[1])
for suffix in ('.js', '.mjs'):
    mimetypes.add_type('text/plain', suffix)
from app.main import app
from fastapi.testclient import TestClient
with TestClient(app) as client:
    for suffix in ('js', 'mjs'):
        response = client.get(f'/assets/module.{suffix}')
        assert response.status_code == 200
        assert response.headers['content-type'].split(';')[0] == 'application/javascript'
'''
    env = dict(os.environ, IVYEA_OPS_DATA_DIR=str(tmp_path / 'data'),
               HERMES_HOME=str(tmp_path / 'hermes'), IVYEA_OPS_SKIP_STARTUP_TASKS='1')
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)],
                            env=env, cwd=Path(__file__).resolve().parents[2],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
