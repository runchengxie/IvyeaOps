"""Public entry points must resolve without installing or stopping anything."""
import json
from pathlib import Path
import shutil
import subprocess
import importlib.util
import os
import re
import pytest

ROOT=Path(__file__).resolve().parents[3]


def test_canonical_docs_and_github_entry_points():
    for name in ('changelog','contributing','security','configuration','installation','operations','integrations','usage','troubleshooting'):
        assert (ROOT/'docs'/f'{name}.md').is_file()
    for name in ('CONTRIBUTING','SECURITY'):
        text=(ROOT/'.github'/f'{name}.md').read_text('utf-8')
        assert f'../docs/{name.lower()}.md' in text
    workflow=(ROOT/'.github/workflows/release.yml').read_text('utf-8')
    assert 'docs/changelog.md' in workflow
    assert '> docs/version' in workflow
    assert '$stage/VERSION' in workflow and '$res/VERSION' in workflow
    assert 'scripts/stop.bat' in workflow and 'scripts/update-bundle.bat' in workflow


@pytest.mark.parametrize('action,target,extra,entry',[
    ('install','source',[],'install.ps1'),
    ('install','bundle',[],'install-exe.ps1'),
    ('start','source',[],'start-hidden.ps1'),
    ('start','source',['-Foreground'],'start-console.ps1'),
    ('start','source',['-Lan'],'start-console.ps1'),
    ('stop','source',[],'stop-hidden.ps1'),
    ('update','bundle',[],'update-exe.ps1'),
])
def test_windows_dispatch_is_side_effect_free_in_dry_run(action,target,extra,entry,tmp_path):
    pwsh=shutil.which('pwsh')
    if not pwsh:pytest.skip('PowerShell unavailable on this runner')
    script=ROOT/'scripts/manage.ps1'
    result=subprocess.run([pwsh,'-NoProfile','-File',str(script),'-Action',action,'-Target',target,*extra,'-DryRun'],
        cwd=tmp_path,capture_output=True,encoding='utf-8',timeout=15)
    assert result.returncode==0,result.stderr
    plan=json.loads(result.stdout.lstrip('\ufeff'))
    assert Path(plan['script']).name==entry
    assert Path(plan['script']).is_file()
    assert plan['executed'] is False
    assert list(tmp_path.iterdir())==[]


def migration_module():
    spec=importlib.util.spec_from_file_location('migrate_layout_config',ROOT/'scripts/migrate-config.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_configuration_copy_is_lossless_and_never_overwrites(tmp_path):
    migrate=migration_module().migrate
    old=tmp_path/'server/.env';old.parent.mkdir();old.write_bytes(b'DEMO=original\n')
    assert migrate(tmp_path)=='migrated'
    current=tmp_path/'src/server/.env'
    assert old.read_bytes()==current.read_bytes()
    current.write_bytes(b'DEMO=custom\n')
    assert migrate(tmp_path)=='existing'
    assert current.read_bytes()==b'DEMO=custom\n' and old.read_bytes()==b'DEMO=original\n'


def test_configuration_publication_failure_leaves_no_partial_file(tmp_path,monkeypatch):
    module=migration_module()
    old=tmp_path/'server/.env';old.parent.mkdir();old.write_bytes(b'DEMO=original\n')
    def fail(*args):raise OSError('synthetic disk failure')
    monkeypatch.setattr(module.os,'link',fail)
    with pytest.raises(OSError):module.migrate(tmp_path)
    assert not (tmp_path/'src/server/.env').exists()
    assert list((tmp_path/'src/server').iterdir())==[]
    assert old.read_bytes()==b'DEMO=original\n'


@pytest.mark.skipif(os.name!='nt',reason='Windows PowerShell 5.1 contract')
def test_native_windows_powershell_parses_entry_chain():
    shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    code="$bad=0;Get-ChildItem -LiteralPath '"+str(ROOT/'scripts').replace("'","''")+"' -Recurse -Filter *.ps1|ForEach-Object{$e=$null;[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$null,[ref]$e)|Out-Null;if($e){$bad+=$e.Count}};exit $bad"
    result=subprocess.run([str(shell),'-NoProfile','-Command',code],capture_output=True,timeout=20)
    assert result.returncode==0


def test_documented_snapshot_is_valid_and_localizations_match():
    from app.services.store_artifacts import StoreSnapshot
    examples=[]
    for relative in ('docs/usage.md','docs/zh-CN/usage.md'):
        text=(ROOT/relative).read_text('utf-8')
        example=json.loads(re.search(r'```json\s*(.*?)```',text,re.S).group(1))
        StoreSnapshot.model_validate(example)
        examples.append(example)
    assert examples[0]==examples[1]


def test_retired_docker_dispatch_is_rejected():
    pwsh=shutil.which('pwsh')
    if not pwsh:
        pytest.skip('PowerShell unavailable on this runner')
    result=subprocess.run([pwsh,'-NoProfile','-File',str(ROOT/'scripts/manage.ps1'),'-Action','setup-docker','-DryRun'],capture_output=True,timeout=15)
    assert result.returncode != 0
