import pytest
from app.services import store_artifacts as artifacts
from app.services import emag_workspace as workspace
from app.services import emag_jobs as jobs


@pytest.fixture
def sample(tmp_path,monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'data_dir',tmp_path)
    def save(price=10):
        return artifacts.import_snapshot({'store_id':'demo-ro','platform':'emag','marketplace':'RO',
          'captured_at':'2026-10-28T00:00:00Z','source':'synthetic','coverage':['offers'],
          'limitations':['not real'],'data':{'offers':[{'id':1,'name':'Example','sale_price':price,
          'general_stock':2,'category_id':7,'offer_validation_status':{'value':1},'validation_status':[{'value':9}]}]}})
    return save


def test_drafts_are_bound_to_real_current_products(sample):
    source=sample()
    draft=workspace.save_draft('demo-ro',source['snapshot_id'],'listing','1','Title','Verified draft','operator')
    assert workspace.view('demo-ro')['drafts'][0]['draft_id']==draft['draft_id']
    with pytest.raises(ValueError):workspace.save_draft('demo-ro',source['snapshot_id'],'listing','999','Title','body','a')
    sample(11)
    with pytest.raises(ValueError):workspace.save_draft('demo-ro',source['snapshot_id'],'listing','1','Title','body','a')
    assert workspace.view('demo-ro')['drafts'][0]['stale'] is True


def test_job_replay_is_explicit_and_report_is_bound(sample):
    source=sample()
    receipt=jobs.run('demo-ro')
    assert receipt['mode']=='existing_snapshot' and receipt['status']=='complete'
    report=artifacts.read_report(receipt['report_id'])
    assert report['snapshot_id']==source['snapshot_id']
    assert jobs.latest('demo-ro')['run_id']==receipt['run_id']


def test_delta_does_not_treat_missing_as_zero():
    changes=jobs.compare([{'id':1,'sale_price':'10.00','general_stock':None}],
                         [{'id':1,'sale_price':10,'general_stock':0}])
    assert len(changes)==1 and changes[0]['field']=='general_stock'
    assert changes[0]['before'] is None


def test_failed_collection_preserves_source_and_records_failure(sample):
    source=sample()
    def fail():raise ValueError('do not log private details')
    receipt=jobs.run('demo-ro',fail)
    assert receipt['status']=='failed' and 'private' not in str(receipt)
    assert artifacts.read_snapshot('demo-ro')['snapshot_id']==source['snapshot_id']


def test_busy_store_never_calls_collector(sample):
    import sqlite3
    sample()
    root=jobs._root('demo-ro');root.mkdir(parents=True)
    lock=sqlite3.connect(root/'run-lock.sqlite3');lock.execute('BEGIN IMMEDIATE')
    called=[]
    try:
        with pytest.raises(sqlite3.OperationalError):jobs.run('demo-ro',lambda:called.append(True))
        assert called==[]
    finally:lock.close()


def test_workspace_routes_require_admin_and_bind_actor(sample):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import require_admin
    from app.routers import emag_operations as module
    import importlib
    source=sample()
    app=FastAPI();app.include_router(importlib.reload(module).router,prefix='/api/emag')
    with TestClient(app) as client:
        url='/api/emag/stores/demo-ro'
        assert client.get(url+'/workspace').status_code==401
        app.dependency_overrides[require_admin]=lambda:'operator'
        payload={'snapshot_id': source['snapshot_id'],'kind': 'listing','product_id': '1','title': 'Title','body': 'Verified'}
        assert client.post(url+'/drafts',json={**payload,'actor':'forged'}).status_code==422
        result=client.post(url+'/drafts',json=payload)
        assert result.status_code==200 and result.json()['actor']=='operator'
        assert client.get(url+'/workspace').json()['drafts'][0]['body']=='Verified'


@pytest.mark.asyncio
async def test_job_status_mcp_is_read_only_and_strict(sample):
    from app.routers import mcp_server
    sample();receipt=jobs.run('demo-ro')
    assert mcp_server.TOOLS['ivyea_emag_job_status']['scope']=='read'
    result=await mcp_server._call_tool('ivyea_emag_job_status',{'store_id':'demo-ro'})
    assert receipt['run_id'] in result['content'][0]['text']
    assert (await mcp_server._call_tool('ivyea_emag_job_status',{'store_id':'demo-ro','run':True}))['isError']
    assert (await mcp_server._call_tool('ivyea_emag_job_status',{'store_id':'../bad'}))['isError']


def test_cli_busy_run_has_safe_exit(sample,capsys):
    import sqlite3
    from app import emag_job_cli
    sample();root=jobs._root('demo-ro');root.mkdir(parents=True)
    lock=sqlite3.connect(root/'run-lock.sqlite3');lock.execute('BEGIN IMMEDIATE')
    try:
        assert emag_job_cli.main(['--store-id','demo-ro','--from-latest'])==2
        assert 'lock' in capsys.readouterr().out
    finally:lock.close()


def test_large_delta_receipt_is_bounded_and_explicit(sample,monkeypatch):
    source=sample()
    changed={**source,'snapshot_id':'new-source','data':{'offers':[dict(source['data']['offers'][0],sale_price=11)]}}
    monkeypatch.setattr(jobs.emag_business,'publish',lambda *args:changed)
    monkeypatch.setattr(jobs,'compare',lambda *args:[{'id': str(i),'field': 'validation_status','before': 'x'*20000,'after': 'y'*20000} for i in range(60)])
    # save_report normally resolves an imported immutable source.
    monkeypatch.setattr(artifacts,'save_report',lambda *args:{'report_id':'synthetic-report'})
    receipt=jobs.run('demo-ro',lambda:{})
    assert receipt['status']=='complete'
    assert receipt['change_count']==60 and receipt['changes_truncated'] is True
    import json
    assert len(json.dumps(jobs.latest('demo-ro')).encode())<100000
