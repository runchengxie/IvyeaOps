import pytest
from app.services import store_artifacts as artifacts
from app.services import emag_operations as ops


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    def save(price=2):
        return artifacts.import_snapshot({'store_id':'demo-ro','platform':'emag','marketplace':'RO',
          'captured_at':'2026-10-28T00:00:00Z','source':'synthetic', 'coverage':['offers'],
          'limitations':['test only'],'data':{'offers':[{'id':1,'general_stock':3,
          'offer_validation_status':{'value':price},'validation_status':[{'value':9}]}]}})
    return save


def test_workflow_is_version_bound_and_review_is_not_resolution(evidence):
    first=evidence()
    item=ops.board('demo-ro')['issues'][0]
    assert item['state']=='pending'
    for revision, state in enumerate(('proposed','approved','executed')):
        item=ops.transition('demo-ro',first['snapshot_id'],item['issue_id'],state,revision,'manual note','admin')
    newer=evidence()
    assert ops.board('demo-ro')['issues'][0]['state']=='pending'
    with pytest.raises(ValueError):
        ops.transition('demo-ro',first['snapshot_id'],item['issue_id'],'reviewed',3,'wrong version','admin',first['snapshot_id'])
    result=ops.transition('demo-ro',first['snapshot_id'],item['issue_id'],'reviewed',3,'checked new evidence','admin',newer['snapshot_id'])
    assert result['review_snapshot_id']==newer['snapshot_id']
    assert result['issue_still_present'] is True


def test_reject_skip_stale_concurrency_and_empty_note(evidence):
    first=evidence(); issue=ops.board('demo-ro')['issues'][0]['issue_id']
    with pytest.raises(ValueError): ops.transition('demo-ro',first['snapshot_id'],issue,'executed',0,'note','a')
    with pytest.raises(ValueError): ops.transition('demo-ro',first['snapshot_id'],issue,'proposed',0,' ','a')
    ops.transition('demo-ro',first['snapshot_id'],issue,'proposed',0,'note','a')
    with pytest.raises(ValueError): ops.transition('demo-ro',first['snapshot_id'],issue,'approved',0,'note','a')
    evidence()
    with pytest.raises(ValueError): ops.transition('demo-ro',first['snapshot_id'],issue,'approved',1,'note','a')


def test_router_requires_admin_and_binds_actor(evidence):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import require_admin
    from app.routers.emag_operations import router
    evidence()
    app=FastAPI(); app.include_router(router,prefix='/api/emag')
    with TestClient(app) as client:
        assert client.get('/api/emag/stores').status_code==401
        app.dependency_overrides[require_admin]=lambda:'operator'
        board=client.get('/api/emag/stores/demo-ro').json()
        issue=board['issues'][0]
        response=client.post('/api/emag/stores/demo-ro/issues/'+issue['issue_id'],json={
            'snapshot_id':board['snapshot_id'],'state':'proposed','revision':0,'note':'test plan'})
        assert response.status_code==200
        assert response.json()['history'][0]['actor']=='operator'


def test_publication_respects_shared_guard(evidence):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    started=Event()
    def publish():
        started.set()
        return evidence()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with artifacts.snapshot_guard():
            future=pool.submit(publish)
            assert started.wait(2)
            assert not future.done()
        assert future.result(timeout=5)['snapshot_id']
