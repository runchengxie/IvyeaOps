"""Installer proxy configuration must remain in its process environment."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _find_bash():
    if os.name == 'nt':
        git_dir = subprocess.run(['git', '--exec-path'], capture_output=True, text=True, check=True).stdout.strip()
        candidates = [Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe',
                      Path(git_dir).parents[2] / 'bin/bash.exe']
        bash = next((str(p) for p in candidates if p.is_file()), None)
    else:
        bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash is unavailable on this host')
    return bash


def test_proxy_preserves_existing_process_config_and_does_not_write_global(tmp_path):
    bash = _find_bash()
    global_file = tmp_path / 'git-global-config'
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(global_file), GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='user.name', GIT_CONFIG_VALUE_0='Existing')
    script = "source \"$1\"; configure_github_proxy 'https://example.invalid/'; git config --get user.name; git config --get 'url.https://example.invalid/https://github.com/.insteadOf'"
    result = subprocess.run([bash, '-c', script, 'bash', (ROOT / 'scripts/github-proxy.sh').as_posix()],
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['Existing', 'https://github.com/']
    assert not global_file.exists()


def test_installer_refuses_old_environment_before_touching_configuration(tmp_path):
    bash = _find_bash()
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copyfile(ROOT / 'scripts/install.sh', scripts / 'install.sh')
    shutil.copyfile(ROOT / 'scripts/check-layout.sh', scripts / 'check-layout.sh')
    server = tmp_path / 'src/server'
    python = server / '.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text('#!/usr/bin/env bash\nexit 1\n', encoding='utf-8')
    python.chmod(0o755)
    env_file = server / '.env'
    env_file.write_text('EXISTING=preserved\n', encoding='utf-8')
    dist = tmp_path / 'src/client/dist'
    dist.mkdir(parents=True)
    (dist / 'index.html').write_text('fixture', encoding='utf-8')
    env = dict(os.environ, IVYEA_CN='0', PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH'])
    result = subprocess.run([bash, (scripts / 'install.sh').as_posix()], cwd=tmp_path, env=env,
                            capture_output=True, encoding="utf-8", timeout=30)
    assert result.returncode != 0
    assert 'existing src/server/.venv requires Python 3.11+' in result.stderr
    assert env_file.read_text(encoding='utf-8') == 'EXISTING=preserved\n'


def test_installer_bootstraps_missing_pip_without_replacing_configuration(tmp_path):
    bash = _find_bash()
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copyfile(ROOT / 'scripts/install.sh', scripts / 'install.sh')
    shutil.copyfile(ROOT / 'scripts/check-layout.sh', scripts / 'check-layout.sh')
    server = tmp_path / 'src/server'
    python = server / '.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text("#!/usr/bin/env bash\ncase \"$*\" in\n  '-c '* ) exit 0 ;;\n  '-m pip --version') exit 1 ;;\n  '-m ensurepip --upgrade') echo ensurepip >> \"$PY_MARKER\"; exit 0 ;;\n  '-m pip install'*) echo install >> \"$PY_MARKER\"; exit 1 ;;\nesac\nexit 1\n", encoding='utf-8')
    python.chmod(0o755)
    env_file = server / '.env'
    env_file.write_text('EXISTING=preserved\n', encoding='utf-8')
    dist = tmp_path / 'src/client/dist'
    dist.mkdir(parents=True)
    (dist / 'index.html').write_text('fixture', encoding='utf-8')
    marker = tmp_path / 'python-calls'
    env = dict(os.environ, IVYEA_CN='0', PY_MARKER=marker.as_posix(),
               PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH'])
    result = subprocess.run([bash, (scripts / 'install.sh').as_posix()], cwd=tmp_path, env=env,
                            capture_output=True, encoding='utf-8', timeout=30)
    assert result.returncode != 0
    assert marker.read_text(encoding='utf-8').splitlines() == ['ensurepip', 'install']
    assert env_file.read_text(encoding='utf-8') == 'EXISTING=preserved\n'


def test_installer_finds_versioned_python_when_default_is_old(tmp_path):
    bash = _find_bash()
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copyfile(ROOT / 'scripts/install.sh', scripts / 'install.sh')
    shutil.copyfile(ROOT / 'scripts/check-layout.sh', scripts / 'check-layout.sh')
    fake_bin = tmp_path / 'fake-bin'
    fake_bin.mkdir()
    for name, minor in (('python', 10), ('python3', 10), ('python3.11', 11)):
        exe = fake_bin / name
        exe.write_text(f"#!/usr/bin/env bash\ncase \"$*\" in *version_info.major*) echo 3;; *version_info.minor*) echo {minor};; *) echo '(3, {minor})';; esac\n", encoding='utf-8')
        exe.chmod(0o755)
    python = tmp_path / 'src/server/.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text('#!/usr/bin/env bash\nexit 1\n', encoding='utf-8')
    python.chmod(0o755)
    dist = tmp_path / 'src/client/dist'
    dist.mkdir(parents=True)
    (dist / 'index.html').write_text('fixture', encoding='utf-8')
    env = dict(os.environ, IVYEA_CN='0', PATH=str(fake_bin) + os.pathsep + os.environ['PATH'])
    result = subprocess.run([bash, (scripts / 'install.sh').as_posix()], cwd=tmp_path, env=env,
                            capture_output=True, encoding='utf-8', timeout=30)
    assert result.returncode != 0
    assert 'existing src/server/.venv requires Python 3.11+' in result.stderr


def test_proxy_accepts_decimal_config_count_with_leading_zero(tmp_path):
    bash = _find_bash()
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(tmp_path / 'global'), GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_COUNT='08')
    for index in range(8):
        env[f'GIT_CONFIG_KEY_{index}'] = f'test.key{index}'
        env[f'GIT_CONFIG_VALUE_{index}'] = str(index)
    script = "source \"$1\"; configure_github_proxy 'https://example.invalid/'; git config --get test.key7; git config --get 'url.https://example.invalid/https://github.com/.insteadOf'"
    result = subprocess.run([bash, '-c', script, 'bash', (ROOT / 'scripts/github-proxy.sh').as_posix()],
                            env=env, capture_output=True, encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['7', 'https://github.com/']
