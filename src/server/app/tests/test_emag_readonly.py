import json
import httpx
import pytest
from app.services import emag_readonly as emag


def collect(bodies, **kwargs):
    requests = []
    def handler(request):
        requests.append(request)
        body = bodies.pop(0)
        return body if isinstance(body, httpx.Response) else httpx.Response(200, json=body)
    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        result = emag.collect(client, httpx.BasicAuth('example', 'secret'), page_size=2, delay=0, **kwargs)
    return result, requests


def ok(rows):
    return {'isError': False, 'results': rows}


def test_fixed_read_endpoint_and_pagination():
    result, requests = collect([ok([{'id': 1}, {'id': 2}]), ok([{'id': 3}])])
    assert result['complete'] and len(result['offers']) == 3
    assert all(str(r.url) == emag.ENDPOINT and r.method == 'POST' for r in requests)
    assert json.loads(requests[1].content) == {'currentPage': 2, 'itemsPerPage': 2}


@pytest.mark.parametrize('bad', [
    {'isError': True, 'results': []}, {'isError': False},
    ok([{'id': 1}]), ok([{}]), ok([{'id': []}]),
    httpx.Response(302, headers={'location': 'https://example.org'}), httpx.Response(429)])
def test_incomplete_or_repeated_pages_stop(bad):
    result, requests = collect([ok([{'id': 1}, {'id': 2}]), bad])
    assert not result['complete']
    assert len(result['offers']) == 2 and len(requests) == 2


def test_page_cap_is_incomplete():
    result, _ = collect([ok([{'id': 1}, {'id': 2}])], max_pages=1)
    assert not result['complete'] and result['reason'] == 'page_limit'


def test_recursive_redaction_preserves_json():
    value = {'nested': ['quote"password and account', {'x': 'quote"password'}]}
    redacted = emag.redact(value, ('quote"password', 'account'))
    assert redacted == {'nested': ['[REDACTED] and [REDACTED]', {'x': '[REDACTED]'}]}


def test_missing_stock_is_unknown_and_multiple_statuses_are_preserved():
    row = {'id': 1, 'status': 1, 'validation_status': [{'value': 9}, {'value': 3}],
           'offer_validation_status': {'value': 2, 'errors': 'Invalid price'}}
    report = emag.summarize([row])
    assert report['stock_unknown'] == 1 and report['stock_zero'] == 0
    assert report['invalid_price'] == 1 and report['invalid_price_with_stock'] == 0
    assert emag.project_offer(row)['validation_status'] == [{'value': 9}, {'value': 3}]


@pytest.mark.parametrize('bad', [None, {}, [], 'invalid', [{'value': '9'}], [{'value': 999}], [{'value': 1}, 'malformed']])
def test_unknown_validation_is_not_healthy(bad):
    result = emag.summarize([{'id': 1, 'validation_status': bad, 'offer_validation_status': bad}])
    assert result['documentation_status_unknown'] == 1
    assert result['price_status_unknown'] == 1


def test_publish_binds_report_to_snapshot(tmp_path, monkeypatch):
    from app.core.config import settings
    from app.services import store_artifacts
    monkeypatch.setattr(settings, 'data_dir', tmp_path)
    result = {'complete': True, 'reason': 'end_of_pagination', 'offers': [{'id': 1}], 'pages': 1}
    receipt = emag.publish('demo-emag-ro', result)
    report = store_artifacts.read_report(receipt['report_id'])
    assert report['snapshot_id'] == receipt['snapshot_id']
    assert report['snapshot']['data']['summary']['stock_unknown'] == 1
    with pytest.raises(ValueError):
        emag.publish('demo-emag-ro', {**result, 'complete': False})


def test_cli_missing_credential_stops_before_network(monkeypatch):
    from app import emag_cli
    def unavailable():
        raise OSError('unavailable')
    monkeypatch.setattr(emag_cli, 'read_emag_credentials', unavailable)
    assert emag_cli.main(['--store-id', 'demo-emag-ro']) == 2
