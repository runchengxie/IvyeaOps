"""Agent versions must be reproducible unless explicitly overridden."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def resolve(env):
    return subprocess.run([sys.executable, str(ROOT / 'scripts/agent-ref.py')],
                          cwd=ROOT, env=env, capture_output=True, encoding='utf-8', timeout=15)


def test_default_agent_ref_is_the_validated_release():
    env = dict(os.environ)
    env.pop('IVYEA_AGENT_REF', None)
    result = resolve(env)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'v1.16.9'


def test_explicit_agent_ref_is_preserved():
    result = resolve(dict(os.environ, IVYEA_AGENT_REF='feature/example'))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'feature/example'


def test_multiline_agent_ref_is_rejected():
    result = resolve(dict(os.environ, IVYEA_AGENT_REF='release\nother'))
    assert result.returncode != 0
