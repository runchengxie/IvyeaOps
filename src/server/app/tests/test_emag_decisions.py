"""Acceptance tests for deterministic, entity-bound eMAG evidence."""
import copy
import pytest
from app.services import emag_decisions as decisions
from app.core.findings import Evidence


def snapshot(stock=0):
    return {'schema_version':1,'store_id':'demo-ro','snapshot_id':'snap-1','platform':'emag','marketplace':'RO',
        'source':'synthetic','captured_at':'2026-10-30T00:00:00Z','coverage':['offers'],'limitations':['test'],
        'data':{'offers':[{'id':1,'part_number':'sku','general_stock':stock,'offer_validation_status':{'value':2}}]}}


def test_zero_missing_and_deterministic_field_references():
    result=decisions.diagnose(snapshot())
    assert result['findings']
    evidence=result['findings'][0]['evidence']
    stock=next(e for e in evidence if e['metric']=='general_stock')
    assert stock['value']==0 and stock['evidence_type']=='observed'
    assert stock['field_path']=='/data/offers/0/general_stock'
    missing=next(e for e in decisions.diagnose(snapshot(None))['findings'][0]['evidence'] if e['metric']=='general_stock')
    assert missing['value'] is None and missing['evidence_type']=='missing' and missing['missing_reason']
    assert decisions.verify(result['findings'][0],snapshot())['valid'] is True


def test_gate_rejects_entity_version_field_and_dependency_forgery():
    snap=snapshot(); finding=decisions.diagnose(snap)['findings'][0]
    for key,value in [('snapshot_id','other'),('store_id','other'),('offer_id','99')]:
        forged=copy.deepcopy(finding);forged['evidence'][0][key]=value
        assert decisions.verify(forged,snap)['valid'] is False
    forged=copy.deepcopy(finding);forged['evidence'][0]['value']='invented'
    assert decisions.verify(forged,snap)['valid'] is False
    forged=copy.deepcopy(finding);forged['evidence'][-1]['derived_from']=['absent']
    assert decisions.verify(forged,snap)['valid'] is False
    newer={**snap,'snapshot_id':'snap-2'}
    assert decisions.verify(finding,newer)['valid'] is False


def test_legacy_evidence_is_not_observed_by_default():
    assert Evidence(metric='legacy_note',value='high stock').evidence_type=='inference'


def test_schema_version_roundtrip_and_old_file(tmp_path,monkeypatch):
    from app.core.config import settings
    from app.services import store_artifacts as artifacts
    monkeypatch.setattr(settings,'data_dir',tmp_path)
    raw=snapshot();raw.pop('snapshot_id');raw.pop('schema_version')
    saved=artifacts.import_snapshot(raw)
    assert saved['schema_version']==1
    import json
    path=artifacts._root()/'snapshots'/'demo-ro'/(saved['snapshot_id']+'.json')
    payload=json.loads(path.read_text('utf-8'));payload.pop('schema_version')
    path.write_text(json.dumps(payload),encoding='utf-8')
    assert artifacts.read_snapshot('demo-ro')['schema_version']==1
    with pytest.raises(ValueError): artifacts.import_snapshot({**raw,'schema_version':99})

def test_missing_label_cannot_hide_observed_zero():
    snap=snapshot();finding=decisions.diagnose(snap)['findings'][0]
    field=next(e for e in finding['evidence'] if e['metric']=='general_stock')
    field.update(evidence_type='missing',value=None,missing_reason='Invented missing value')
    assert decisions.verify(finding,snap)['valid'] is False

def test_report_proposal_and_review_share_field_evidence(tmp_path,monkeypatch):
    from app.core.config import settings
    from app.services import store_artifacts as artifacts, emag_jobs, emag_operations
    monkeypatch.setattr(settings,'data_dir',tmp_path)
    raw=snapshot();raw.pop('snapshot_id')
    saved=artifacts.import_snapshot(raw)
    result=emag_jobs.run('demo-ro')
    assert result['status']=='complete' and result['decision_gate']['model_used'] is False
    report=artifacts.read_report(result['report_id'])
    assert '/data/offers/0/general_stock' in report['markdown']
    issue=emag_operations.board('demo-ro')['issues'][0]
    proposed=emag_operations.transition('demo-ro',saved['snapshot_id'],issue['issue_id'],'proposed',0,'Check status','operator')
    assert proposed['diagnosis']['snapshot_id']==saved['snapshot_id']
    newer=artifacts.import_snapshot(raw)
    with pytest.raises(ValueError):
        emag_operations.transition('demo-ro',saved['snapshot_id'],issue['issue_id'],'approved',1,'Old approval','operator')
    assert newer['snapshot_id']!=saved['snapshot_id']

def test_invalid_stock_cannot_be_promoted_to_observed():
    snap=snapshot(-1);finding=decisions.diagnose(snap)['findings'][0]
    stock=next(e for e in finding['evidence'] if e['metric']=='general_stock')
    stock.update(evidence_type='observed',value=-1,missing_reason='')
    assert decisions.verify(finding,snap)['valid'] is False


def test_action_cannot_bypass_diagnosis_or_change_registered_meaning():
    snap=snapshot();finding=decisions.diagnose(snap)['findings'][0]
    finding['actions'][0].update(required_evidence=['general_stock'],detail='Raise price because margin is low')
    assert decisions.verify(finding,snap)['valid'] is False


def test_proposal_cannot_pass_after_its_diagnostic_field_is_tampered(tmp_path,monkeypatch):
    from app.core.config import settings
    from app.services import store_artifacts as artifacts, emag_operations
    import json
    monkeypatch.setattr(settings,'data_dir',tmp_path)
    raw=snapshot();raw.pop('snapshot_id');saved=artifacts.import_snapshot(raw)
    issue=emag_operations.board('demo-ro')['issues'][0]
    proposal=emag_operations.transition('demo-ro',saved['snapshot_id'],issue['issue_id'],'proposed',0,'Review','operator')
    proposal['diagnosis']['evidence'][0]['value']={'value':1}
    with emag_operations._connect() as conn:
        conn.execute('UPDATE records SET payload=? WHERE store=? AND snapshot=? AND issue=?',
            (json.dumps(proposal),'demo-ro',saved['snapshot_id'],issue['issue_id']))
    with pytest.raises(ValueError):
        emag_operations.transition('demo-ro',saved['snapshot_id'],issue['issue_id'],'approved',1,'Approve','operator')
