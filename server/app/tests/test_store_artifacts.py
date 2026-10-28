import importlib
import pytest


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, 'data_dir', tmp_path)
    from app.services import store_artifacts
    return importlib.reload(store_artifacts)


def snapshot():
    return {'store_id':'demo-emag-ro', 'platform':'emag', 'marketplace':'RO',
            'captured_at':'2026-10-28T02:00:00Z', 'source':'manual-dashboard',
            'coverage':['dashboard'], 'limitations':['Orders not checked'],
            'data':{'seller_rating':4.9}}


def test_snapshot_roundtrip_and_missing(artifacts):
    with pytest.raises(FileNotFoundError):
        artifacts.read_snapshot('demo-emag-ro')
    saved = artifacts.import_snapshot(snapshot())
    assert artifacts.read_snapshot('demo-emag-ro') == saved
    assert saved['data'] == {'seller_rating':4.9}
    assert saved['limitations'] == ['Orders not checked']


@pytest.mark.parametrize('field,value', [('store_id','../outside'), ('captured_at','yesterday'),
    ('captured_at','2026-10-28T02:00:00'), ('source',''), ('extra','unexpected')])
def test_invalid_snapshot_is_rejected(artifacts, field, value):
    payload = snapshot()
    payload[field] = value
    with pytest.raises(ValueError):
        artifacts.import_snapshot(payload)


def test_report_is_immutable_and_linked_to_snapshot(artifacts):
    artifacts.import_snapshot(snapshot())
    snapshot_id = artifacts.read_snapshot('demo-emag-ro')['snapshot_id']
    saved = artifacts.save_report('demo-emag-ro', snapshot_id, 'Initial audit', 'Partial coverage; verify identity.')
    assert artifacts.read_report(saved['report_id']) == saved
    assert saved['snapshot_captured_at'] == snapshot()['captured_at']
    second = artifacts.save_report('demo-emag-ro', snapshot_id, 'Followup', 'Check payments.')
    assert second['report_id'] != saved['report_id']
    with pytest.raises(ValueError):
        artifacts.read_report('../outside')
    with pytest.raises(FileNotFoundError):
        artifacts.save_report('missing-store', snapshot_id, 'Audit', 'No source')


def test_new_snapshot_does_not_change_report_evidence(artifacts):
    original = artifacts.import_snapshot(snapshot())
    newer = snapshot()
    newer['data'] = {'seller_rating':3.0}
    artifacts.import_snapshot(newer)
    report = artifacts.save_report('demo-emag-ro', original['snapshot_id'], 'Audit', 'Evidence')
    assert artifacts.read_report(report['report_id'])['snapshot'] == original
    for invalid_id in ('', None, '../outside'):
        with pytest.raises(ValueError):
            artifacts.save_report('demo-emag-ro', invalid_id, 'Audit', 'Evidence')


def test_failed_publish_leaves_no_partial_snapshot(artifacts, monkeypatch):
    def fail(source, destination):
        assert not destination.exists()
        assert artifacts.json.loads(source.read_text('utf-8'))['store_id'] == 'demo-emag-ro'
        raise PermissionError('simulated publish failure')
    monkeypatch.setattr(artifacts.os, 'replace', fail)
    with pytest.raises(PermissionError):
        artifacts.import_snapshot(snapshot())
    assert not list(artifacts._root().rglob('*.json'))
    assert not list(artifacts._root().rglob('*.tmp'))
