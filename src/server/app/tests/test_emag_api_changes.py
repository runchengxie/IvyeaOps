"""No real credentials, merchant data or network writes are used here."""
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.services import store_artifacts


@pytest.fixture
def case(tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    monkeypatch.setattr(settings, 'emag_writes_enabled', True, raising=False)
    monkeypatch.setattr(settings, 'emag_write_store_id', 'demo-ro', raising=False)
    offer = {'id': 9000000000001, 'part_number': 'sku-1', 'part_number_key': 'DTEST0001',
             'currency': 'RON', 'sale_price': '119', 'min_sale_price': '2',
             'max_sale_price': '300', 'general_stock': 3, 'status': 1,
             'offer_validation_status': {'value': 2}, 'validation_status': [{'value': 9}]}

    def snapshot(**changes):
        return store_artifacts.import_snapshot({'store_id': 'demo-ro', 'platform': 'emag',
            'marketplace': 'RO', 'captured_at': datetime.now(timezone.utc).isoformat(),
            'source': 'https://marketplace-api.emag.ro/api-3/', 'coverage': ['offers'],
            'limitations': ['Synthetic test only'], 'data': {'offers': [{**offer, **changes}]}})

    return snapshot, offer


def prepared(case, price='120'):
    from app.services import emag_api_changes as svc
    make, _ = case
    s = make()
    p = svc.prepare('demo-ro', s['snapshot_id'], '9000000000001', {'sale_price': price}, 'admin')
    return svc, s, p


def approved(case, price='120'):
    svc, s, p = prepared(case, price)
    return svc, s, svc.approve('demo-ro', p['proposal_id'], p['digest'], 'Exact price reviewed', 'reviewer')


def execute(svc, p, handler):
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        return svc.execute('demo-ro', p['proposal_id'], p['digest'], True, 'admin', client, ('user', 'secret'))


def test_preview_and_approval_are_local_and_digest_bound(case):
    svc, s, p = prepared(case)
    assert p['state'] == 'prepared'
    assert p['before']['sale_price'] == '119'
    assert p['after'] == {'sale_price': '120'}
    assert p['price_basis'] == 'exclusive_vat'
    assert p['snapshot_id'] == s['snapshot_id']
    assert len(p['digest']) == 64
    with pytest.raises(ValueError):
        svc.approve('demo-ro', p['proposal_id'], '0' * 64, 'wrong digest', 'admin')
    assert svc.approve('demo-ro', p['proposal_id'], p['digest'], 'reviewed', 'reviewer')['state'] == 'approved'


@pytest.mark.parametrize('changes', [
    {'sale_price': True}, {'sale_price': 'NaN'}, {'sale_price': 'Infinity'},
    {'sale_price': 0}, {'sale_price': -1}, {'sale_price': '120.12345'},
    {'sale_price': '119'}, {'sale_price': '301'}, {'sale_price': '1'},
    {'general_stock': 1}, {'name': 'Changed'}, {'status': 0}, {},
])
def test_invalid_or_unsupported_changes_rejected(case, changes):
    from app.services import emag_api_changes as svc
    make, _ = case
    s = make()
    with pytest.raises(ValueError):
        svc.prepare('demo-ro', s['snapshot_id'], '9000000000001', changes, 'admin')


@pytest.mark.parametrize('change', [
    {'currency': 'EUR'}, {'min_sale_price': None}, {'max_sale_price': 'bad'},
    {'part_number_key': ''}, {'id': True},
])
def test_incomplete_or_wrong_entity_evidence_rejected(case, change):
    from app.services import emag_api_changes as svc
    make, _ = case
    s = make(**change)
    with pytest.raises(ValueError):
        svc.prepare('demo-ro', s['snapshot_id'], str(change.get('id', 9000000000001)), {'sale_price': 120}, 'admin')


def test_new_snapshot_invalidates_approval_and_execution(case):
    svc, _, p = prepared(case)
    case[0]()
    with pytest.raises(ValueError):
        svc.approve('demo-ro', p['proposal_id'], p['digest'], 'reviewed', 'admin')


def test_execution_disabled_and_store_binding_gate_before_network(case, monkeypatch):
    from app.core.config import settings
    svc, _, p = approved(case)
    monkeypatch.setattr(settings, 'emag_writes_enabled', False)
    def never(req):
        pytest.fail('No network call is allowed while execution is disabled')
    with pytest.raises(ValueError):
        execute(svc, p, never)
    monkeypatch.setattr(settings, 'emag_writes_enabled', True)
    monkeypatch.setattr(settings, 'emag_write_store_id', 'another-store')
    with pytest.raises(ValueError):
        execute(svc, p, never)


def test_exact_single_offer_body_readback_and_no_replay(case):
    svc, _, p = approved(case)
    calls = []
    live = dict(case[1])
    def handler(req):
        calls.append(req.url.path)
        assert req.url.host == 'marketplace-api.emag.ro'
        if req.url.path.endswith('/offer/save'):
            assert json.loads(req.content) == {'data': [{'id': 9000000000001, 'sale_price': 120.0}]}
            live['sale_price'] = '120'
            return httpx.Response(200, json={'isError': False})
        assert json.loads(req.content) == {'id': 9000000000001, 'currentPage': 1, 'itemsPerPage': 100}
        return httpx.Response(200, json={'isError': False, 'results': [live]})
    receipt = execute(svc, p, handler)
    assert receipt['state'] == 'verified'
    assert receipt['saleability_verified'] is False
    assert receipt['observed']['offer_validation_status'] == {'value': 2}
    assert calls.count('/api-3/offer/save') == 1
    with pytest.raises(ValueError):
        execute(svc, p, handler)
    assert calls.count('/api-3/offer/save') == 1


@pytest.mark.parametrize('drift', [
    {'id': 99}, {'part_number': 'other'}, {'part_number_key': 'DOTHER001'},
    {'part_number': ' sku-1'}, {'part_number': 'sku-1 '},
    {'part_number_key': ' DTEST0001'}, {'part_number_key': 'DTEST0001 '},
    {'currency': 'EUR'}, {'sale_price': '118'}, {'min_sale_price': '3'}, {'max_sale_price': '301'},
])
def test_live_preflight_drift_never_writes(case, drift):
    svc, _, p = approved(case)
    def handler(req):
        assert req.url.path.endswith('/product_offer/read')
        return httpx.Response(200, json={'isError': False, 'results': [{**case[1], **drift}]})
    assert execute(svc, p, handler)['state'] == 'preflight_failed'


@pytest.mark.parametrize('mode', ['timeout', 'redirect', 'invalid_json', 'api_error', 'http_error'])
def test_ambiguous_write_blocks_resend_and_redacts_response(case, mode):
    svc, _, p = approved(case)
    writes = []
    def handler(req):
        if req.url.path.endswith('/offer/save'):
            writes.append(1)
            if mode == 'timeout':
                raise httpx.ReadTimeout('secret in transport error', request=req)
            if mode == 'redirect':
                return httpx.Response(302, headers={'location': 'https://other.invalid'})
            if mode == 'invalid_json':
                return httpx.Response(200, text='secret not JSON')
            return httpx.Response(500 if mode == 'http_error' else 200,
                                  json={'isError': True, 'messages': ['secret']})
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    r = execute(svc, p, handler)
    assert r['state'] == 'uncertain'
    assert 'secret' not in json.dumps(svc.listing('demo-ro'))
    with pytest.raises(ValueError):
        execute(svc, p, handler)
    assert len(writes) == 1


def test_accepted_but_unmatched_readback_needs_read_only_reconciliation(case):
    svc, _, p = approved(case)
    def handler(req):
        if req.url.path.endswith('/offer/save'):
            return httpx.Response(200, json={'isError': False})
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    assert execute(svc, p, handler)['state'] == 'submitted_unverified'
    def read_only(req):
        assert req.url.path.endswith('/product_offer/read')
        return httpx.Response(200, json={'isError': False, 'results': [{**case[1], 'sale_price': '120'}]})
    with httpx.Client(transport=httpx.MockTransport(read_only)) as client:
        r = svc.reconcile('demo-ro', p['proposal_id'], 'admin', client, ('user', 'secret'))
    assert r['state'] == 'verified'
    assert r['submission_status'] == 'accepted'


def test_two_approved_proposals_cannot_submit_concurrently(case):
    svc, s, p = approved(case)
    other = svc.prepare('demo-ro', s['snapshot_id'], '9000000000001', {'sale_price': 121}, 'admin')
    other = svc.approve('demo-ro', other['proposal_id'], other['digest'], 'reviewed', 'admin')
    first_read = True
    live = dict(case[1])
    def handler(req):
        nonlocal first_read
        if req.url.path.endswith('/offer/save'):
            live['sale_price'] = '120'
            return httpx.Response(200, json={'isError': False})
        if first_read:
            first_read = False
            with pytest.raises(ValueError):
                execute(svc, other, handler)
        return httpx.Response(200, json={'isError': False, 'results': [live]})
    assert execute(svc, p, handler)['state'] == 'verified'


def test_snapshot_changes_during_preflight_blocks_post(case):
    svc, _, p = approved(case)
    def handler(req):
        assert req.url.path.endswith('/product_offer/read')
        case[0]()
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    assert execute(svc, p, handler)['state'] == 'preflight_failed'


def test_crash_after_claim_remains_blocked_and_readback_does_not_resend(case):
    svc, s, p = approved(case)
    def crash(req):
        if req.url.path.endswith('/offer/save'):
            raise RuntimeError('Simulated process interruption')
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    with pytest.raises(RuntimeError):
        execute(svc, p, crash)
    row = svc.listing('demo-ro')['proposals'][0]
    assert row['state'] == 'submitting'
    assert row['marketplace_write_attempted'] is True
    assert row['submission_status'] == 'uncertain'
    with pytest.raises(ValueError):
        execute(svc, p, crash)
    other = svc.prepare('demo-ro', s['snapshot_id'], p['product_id'], {'sale_price': 121}, 'admin')
    other = svc.approve('demo-ro', other['proposal_id'], other['digest'], 'reviewed', 'admin')
    with pytest.raises(ValueError):
        execute(svc, other, crash)


def test_uncertain_delivery_is_not_cleared_by_matching_readback(case):
    svc, _, p = approved(case)
    def handler(req):
        if req.url.path.endswith('/offer/save'):
            raise httpx.ReadTimeout('unknown delivery', request=req)
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    assert execute(svc, p, handler)['state'] == 'uncertain'
    def read(req):
        assert req.url.path.endswith('/product_offer/read')
        return httpx.Response(200, json={'isError': False, 'results': [{**case[1], 'sale_price': '120'}]})
    with httpx.Client(transport=httpx.MockTransport(read)) as client:
        r = svc.reconcile('demo-ro', p['proposal_id'], 'admin', client, ('user', 'secret'))
    assert r['observed_price_matches'] is True
    assert r['state'] == 'uncertain'


def test_stale_approved_proposal_and_missing_confirmation_cannot_execute(case):
    svc, _, p = approved(case)
    def never(req):
        pytest.fail('A rejected request reached the network')
    with httpx.Client(transport=httpx.MockTransport(never)) as client:
        with pytest.raises(ValueError):
            svc.execute('demo-ro', p['proposal_id'], p['digest'], False, 'admin', client, None)
    case[0]()
    with pytest.raises(ValueError):
        execute(svc, p, never)


def test_live_factory_preserves_environment_proxy_configuration(case, monkeypatch):
    svc, _, p = approved(case)
    from app.services import windows_credentials
    monkeypatch.setattr(windows_credentials, 'read_emag_credentials', lambda: ('user', 'secret'))
    class Dummy:
        def __init__(self, **kwargs):
            assert 'transport' not in kwargs, 'An explicit transport bypasses environment proxy selection'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr(svc.httpx, 'Client', Dummy)
    monkeypatch.setattr(svc, 'execute', lambda *args: {'state': 'synthetic'})
    assert svc.live_execute('demo-ro', p['proposal_id'], p['digest'], True, 'admin')['state'] == 'synthetic'


def test_concurrent_reconciliation_cannot_overwrite_newer_verified_receipt(case):
    svc, _, p = approved(case)
    def submit(req):
        return httpx.Response(200, json={'isError': False} if req.url.path.endswith('/offer/save')
                              else {'isError': False, 'results': [case[1]]})
    assert execute(svc, p, submit)['state'] == 'submitted_unverified'
    def latest(req):
        return httpx.Response(200, json={'isError': False, 'results': [{**case[1], 'sale_price': '120'}]})
    def delayed(req):
        with httpx.Client(transport=httpx.MockTransport(latest)) as inner:
            assert svc.reconcile('demo-ro', p['proposal_id'], 'other-admin', inner, None)['state'] == 'verified'
        return httpx.Response(200, json={'isError': False, 'results': [case[1]]})
    with httpx.Client(transport=httpx.MockTransport(delayed)) as client, pytest.raises(ValueError):
        svc.reconcile('demo-ro', p['proposal_id'], 'admin', client, None)
    assert svc.listing('demo-ro')['proposals'][0]['state'] == 'verified'


def test_admin_api_preview_approval_and_strict_execution_confirmation(case, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.security import require_admin
    from app.routers import emag_api_changes as routes
    make, _ = case
    s = make()
    app = FastAPI()
    app.include_router(routes.router, prefix='/api/emag')
    client = TestClient(app)
    base = '/api/emag/stores/demo-ro/api-changes'
    assert client.get(base).status_code == 401
    app.dependency_overrides[require_admin] = lambda: 'admin'
    r = client.post(base, json={'snapshot_id': s['snapshot_id'], 'product_id': '9000000000001', 'changes': {'sale_price': '120'}})
    assert r.status_code == 200
    p = r.json()
    url = f'{base}/{p["proposal_id"]}'
    assert client.post(url + '/approve', json={'digest': p['digest'], 'note': 'reviewed'}).status_code == 200
    monkeypatch.setattr(routes.service, 'live_execute', lambda *args: pytest.fail('Invalid confirmation reached execution'))
    assert client.post(url + '/execute', json={'digest': p['digest'], 'confirmed': 'true'}).status_code == 422
    assert client.post(url + '/execute', json={'digest': p['digest'], 'confirmed': False}).status_code == 409
