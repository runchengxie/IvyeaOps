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


def test_audit_report_includes_bounded_source_labelled_issue_details(sample):
    source=sample()
    receipt=jobs.run('demo-ro')
    text=artifacts.read_report(receipt['report_id'])['markdown']
    assert 'Issue details' in text
    assert 'first observed' in text.lower()
    assert 'demo-ro' in text
    assert 'baseline unavailable' in text.lower()


def test_audit_issue_history_ignores_incompatible_and_future_evidence():
    from app.services import emag_audit
    def snap(at, value, source='api'):
        return {'snapshot_id': at.replace(':','').replace('-',''), 'store_id':'demo-ro',
                'platform':'emag','marketplace':'RO','source':source,'coverage':['offers'],
                'captured_at':at,'data':{'offers':[{'id':1,'part_number':'SKU-1',
                'general_stock':3,'offer_validation_status':{'value':value,'errors':'price rejected'}}]}}
    current=snap('2026-10-28T00:00:00+00:00',2)
    older=snap('2026-10-27T00:00:00+00:00',2)
    future=snap('2026-10-29T00:00:00+00:00',2)
    foreign=snap('2026-10-20T00:00:00+00:00',2,'different-source')
    text=emag_audit.render_issues(current,[older,future,foreign],None,history_incomplete=False)
    assert 'SKU-1' in text and 'price rejected' in text and '2026-10-27' in text
    assert '2026-10-20' not in text and '2026-10-29' not in text
    assert 'baseline unavailable' in text.lower()


def test_audit_report_bounds_output_and_escapes_platform_text():
    from app.services import emag_audit
    offers=[{'id':i,'part_number':'sku|<script>' + '<'*1000, 'general_stock':1,
             'offer_validation_status':{'value':2,'errors':'<img src=x> ' + '<'*5000}}
            for i in range(250)]
    snap={'store_id':'demo-ro','platform':'emag','marketplace':'RO','source':'api',
          'coverage':['offers'],'captured_at':'2026-10-28T00:00:00+00:00','data':{'offers':offers}}
    text=emag_audit.render_issues(snap,[],None,history_incomplete=True)
    assert 'Issue details truncated: True' in text and 'History scan incomplete: True' in text
    assert '<script>' not in text and '<img' not in text and '&#124;' in text
    assert len(text) < 150000


def test_audit_treats_legacy_markdown_as_literal_text():
    import markdown
    from app.services import emag_audit
    snap={'store_id':'demo-ro','platform':'emag','marketplace':'RO','source':'api','coverage':['offers'],
          'captured_at':'2026-10-28T00:00:00+00:00','data':{'offers':[{'id':1,
          'part_number':'![tracking](https://example.invalid/pixel)',
          'offer_validation_status':{'value':2,'errors':'[link](https://example.invalid/)'}}]}}
    html = markdown.markdown(emag_audit.render_issues(snap,[],None,history_incomplete=False), extensions=['tables'])
    assert '<img' not in html and '<a ' not in html


def test_audit_keeps_actionable_platform_extra_info():
    from app.services import emag_audit
    snap={'store_id':'demo-ro','platform':'emag','marketplace':'RO','source':'api','coverage':['offers'],
          'captured_at':'2026-10-28T00:00:00+00:00','data':{'offers':[{'id':1,
          'validation_status':[{'value':8, 'error_details':[{'message':'Other reasons',
          'extra_info':'Correct product type'}]}]}]}}
    assert 'Correct product type' in emag_audit.render_issues(snap,[],None,history_incomplete=False)


def test_full_audit_does_not_render_untrusted_source_links(tmp_path, monkeypatch):
    import markdown
    from app.core.config import settings
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    artifacts.import_snapshot({'store_id':'demo-ro','platform':'emag','marketplace':'RO',
        'captured_at':'2026-10-28T00:00:00Z','source':'synthetic','coverage':['offers'],
        'limitations':['![tracking](https://example.invalid/pixel)'],
        'data':{'offers':[{'id':'![tracking](https://example.invalid/)',
                           'offer_validation_status':{'value':2}}]}})
    receipt=jobs.run('demo-ro')
    html=markdown.markdown(artifacts.read_report(receipt['report_id'])['markdown'], extensions=['tables'])
    assert '<img' not in html and '<a ' not in html


def test_audit_history_skips_invalid_snapshot_and_marks_incomplete(sample):
    from app.services import emag_audit
    previous=sample()
    path=artifacts._root() / 'snapshots' / 'demo-ro' / (previous['snapshot_id'] + '.json')
    path.write_text('{invalid', encoding='utf-8')
    current=sample()
    entries, incomplete=emag_audit.history(current)
    assert entries == [] and incomplete
    assert jobs.run('demo-ro')['status'] == 'complete'


def test_audit_reports_previously_observed_issues_without_claiming_resolution():
    from app.services import emag_audit
    baseline={'store_id':'demo-ro','snapshot_id':'old','platform':'emag','marketplace':'RO','source':'api',
              'coverage':['offers'],'captured_at':'2026-10-27T00:00:00+00:00',
              'data':{'offers':[{'id':1,'part_number':'sku-one','offer_validation_status':{'value':2}}]}}
    current={**baseline,'snapshot_id':'new','captured_at':'2026-10-28T00:00:00+00:00',
             'data':{'offers':[]}}
    text=emag_audit.render_issues(current,[baseline],baseline,history_incomplete=False)
    assert 'sku-one' in text and 'not observed in current snapshot' in text.lower()
    assert 'resolved' not in text.lower().replace('does not prove the issue is new or resolved', '')


def test_delta_does_not_treat_missing_as_zero():
    changes=jobs.compare([{'id':1,'sale_price':'10.00','general_stock':None}],
                         [{'id':1,'sale_price':10,'general_stock':0}])
    assert len(changes)==1 and changes[0]['field']=='general_stock'
    assert changes[0]['before'] is None


def test_new_validation_detail_does_not_make_legacy_snapshot_look_changed():
    old = [{'id': 1, 'validation_status': [{'value': 8, 'errors': 'Structured validation details omitted; inspect seller portal.'}]}]
    new = [{'id': 1, 'validation_status': [{**old[0]['validation_status'][0],
        'error_details': [{'code': 'naming:comment', 'message': 'Fix name'}]}]}]
    assert jobs.compare(old, new) == []
    later = [{'id': 1, 'validation_status': [{**new[0]['validation_status'][0],
        'error_details': [{'code': 'naming:comment', 'message': 'Fix type'}]}]}]
    assert jobs.compare(new, later)[0]['field'] == 'validation_status'


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


def test_language_headers_do_not_change_workspace_facts(sample):
    import importlib
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import require_admin
    from app.routers import emag_operations as module
    sample()
    app=FastAPI();app.include_router(importlib.reload(module).router,prefix='/api/emag')
    app.dependency_overrides[require_admin]=lambda:'operator'
    with TestClient(app) as client:
        bodies=[]
        for locale in ('en-US','zh-CN','unknown-locale'):
            response=client.get('/api/emag/stores/demo-ro/workspace',headers={'Accept-Language':locale})
            assert response.status_code==200
            bodies.append(response.json())
        assert bodies[0]==bodies[1]==bodies[2]
