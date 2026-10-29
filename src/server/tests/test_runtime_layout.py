from pathlib import Path
import subprocess
import sys
from app.core.layout import code_root, environment_file
from app.core.version import runtime_root


def test_source_root_and_code_are_distinct():
    root=Path(__file__).resolve().parents[3]
    assert runtime_root()==root
    assert code_root(root)==root/'src'
    assert (code_root(root)/'client/src/App.tsx').is_file()


def test_bundle_layout_remains_compatible(tmp_path):
    (tmp_path/'server').mkdir()
    assert code_root(tmp_path)==tmp_path
    (tmp_path/'src/server').mkdir(parents=True)
    assert code_root(tmp_path)==tmp_path/'src'


def test_existing_ignored_environment_is_not_lost(tmp_path):
    (tmp_path/'src/server').mkdir(parents=True)
    old=tmp_path/'server/.env';old.parent.mkdir();old.write_text('OLD=preserved',encoding='utf-8')
    assert environment_file(tmp_path)==old
    current=tmp_path/'src/server/.env';current.write_text('NEW=preferred',encoding='utf-8')
    assert environment_file(tmp_path)==current


def test_application_rejects_unsupported_python_before_loading_services():
    root = Path(__file__).resolve().parents[1]
    script = "import sys; sys.version_info = (3, 10, 0); import app"
    result = subprocess.run([sys.executable, '-c', script], cwd=root, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert 'Python 3.11 or newer is required' in result.stderr
