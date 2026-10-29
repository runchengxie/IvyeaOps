"""SKU reads are narrow evidence, never complete snapshots."""
import json
import httpx
import pytest
from app.services import emag_readonly as emag


def run(rows):
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json={"isError":False,"results":rows})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result=emag.lookup_sku(client,httpx.BasicAuth("user","secret"),"tabsx30")
    return result,requests


def test_sku_read_uses_documented_filter_and_returns_projected_evidence():
    result,requests=run([{"id":123,"part_number":"tabsx30","name":"example","description":"private document"}])
    assert json.loads(requests[0].content)=={"part_number":"tabsx30","currentPage":1,"itemsPerPage":100}
    assert str(requests[0].url)==emag.ENDPOINT
    assert result["status"]=="found" and result["offer"]["id"]==123
    assert result['evidence_truncated'] is False
    assert "description" not in result["offer"]


def test_sku_read_reports_empty_without_asserting_delisting():
    result,_=run([])
    assert result["status"]=="not_found" and result["offer"] is None


@pytest.mark.parametrize("rows", [[{"id":1,"part_number":"other"}], [{"id":1,"part_number":"tabsx30"},{"id":2,"part_number":"tabsx30"}], [{"part_number":"tabsx30"}]])
def test_sku_read_fails_closed_on_unexpected_or_ambiguous_results(rows):
    result,_=run(rows)
    assert result["status"]=="incomplete" and result["offer"] is None


@pytest.mark.parametrize("sku", ["", " ", "a\nb", "x"*257])
def test_invalid_sku_is_rejected_without_network(sku):
    with httpx.Client(transport=httpx.MockTransport(lambda _: pytest.fail("network request"))) as client:
        with pytest.raises(ValueError):
            emag.lookup_sku(client,httpx.BasicAuth("user","secret"),sku)


def test_http_failure_is_incomplete():
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(429))) as client:
        result=emag.lookup_sku(client,httpx.BasicAuth('user','secret'),'tabsx30')
    assert result=={'status':'incomplete','reason':'http_429','offer':None}


def test_cli_sku_mode_does_not_publish_snapshot(monkeypatch, capsys):
    from app import emag_cli
    monkeypatch.setattr(emag_cli, 'read_emag_credentials', lambda: ('user','secret'))
    monkeypatch.setattr(emag, 'publish', lambda *_: pytest.fail('must not import a snapshot'))
    monkeypatch.setattr(emag, 'lookup_sku', lambda client, auth, sku: {'status':'found','reason':'exact_match','offer':{'part_number':sku, 'name':'secret'}})
    assert emag_cli.main(['--sku','tabsx30'])==0
    output=json.loads(capsys.readouterr().out)
    assert output['scope']=='single_sku_read_only' and output['offer']['name']=='[REDACTED]'
    assert output['captured_at'] and output['status']=='found'


def test_cli_rejects_sku_with_store_id_before_reading_credentials(monkeypatch):
    from app import emag_cli
    monkeypatch.setattr(emag_cli, 'read_emag_credentials', lambda: pytest.fail('credential read'))
    assert emag_cli.main(['--sku','tabsx30','--store-id','example'])==2


def test_describe_sku_mode_is_offline_and_reports_no_writes(monkeypatch, capsys):
    from app import emag_cli
    monkeypatch.setattr(emag_cli, 'read_emag_credentials', lambda: pytest.fail('credential read'))
    assert emag_cli.main(['--describe','--sku','example']) == 0
    output=json.loads(capsys.readouterr().out)
    assert output['filter']=='part_number' and output['writes']=='none'


@pytest.mark.parametrize('response', [httpx.Response(302, headers={'location':'https://example.invalid'}),
                                     httpx.Response(200, json={'isError': True, 'results': []}),
                                     httpx.Response(200, text='not-json')])
def test_sku_failure_never_reports_not_found(response):
    with httpx.Client(transport=httpx.MockTransport(lambda _: response),follow_redirects=True) as client:
        result=emag.lookup_sku(client,httpx.BasicAuth('user','secret'),'tabsx30')
    assert result['status']=='incomplete' and result['offer'] is None


def test_cli_secret_colliding_with_status_cannot_change_control_fields(monkeypatch, capsys):
    from app import emag_cli
    monkeypatch.setattr(emag_cli, 'read_emag_credentials', lambda: ('status','incomplete'))
    monkeypatch.setattr(emag, 'lookup_sku', lambda *_: {'status':'incomplete','reason':'http_429','offer':None})
    assert emag_cli.main(['--sku','tabsx30']) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'incomplete'


def test_sku_evidence_excludes_nested_or_unbounded_platform_values():
    result,_=run([{'id':123,'part_number':'tabsx30','name':'x'*10000,
                   'brand':{'description':'PRIVATE'},
                   'validation_status':[{'value':8,'description':{'private':'document'}}]*40}])
    offer=result['offer']
    assert result['evidence_truncated'] is True
    assert len(offer['name']) <= 256
    assert 'brand' not in offer
    assert len(offer['validation_status']) <= 8
    assert 'PRIVATE' not in json.dumps(offer) and 'document' not in json.dumps(offer)
