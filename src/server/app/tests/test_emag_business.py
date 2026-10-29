import httpx
import pytest
from app.services import emag_business as business


def test_credentials_are_redacted_before_validation_message_is_shortened(monkeypatch):
    row = {'id': 1, 'validation_status': [{'value': 8, 'errors': {'errors': [
        {'message': {'en_GB': 'x' * 252 + 'secretlong'}}]}}]}
    monkeypatch.setattr(business.emag_readonly, 'collect', lambda *args: {'complete': True, 'offers': [row]})
    monkeypatch.setattr(business, 'read_resource', lambda *args, **kwargs: [])
    result = business.collect(None, None, secrets=('secretlong',))
    message = result['data']['offers'][0]['validation_status'][0]['error_details'][0]['message']
    assert 'secr' not in message


def test_read_only_filters_nested_invoice_and_projection():
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json={'isError':False,'results':{'total_results':1,'invoices':[{
            'category':'FC','number':'test','currency':'RON','total_with_vat':'12.34',
            'customer':{'name':'PRIVATE'},'supplier':{'iban':'PRIVATE'},'lines':[]}]}})
    with httpx.Client(transport=httpx.MockTransport(handler),follow_redirects=True) as client:
        rows=business.read_resource(client,None,'invoices',{'date_start':'2026-10-01'},delay=0)
    assert len(rows)==1 and 'customer' not in rows[0] and 'supplier' not in rows[0]
    assert all(r.url.path=='/api-3/invoice/read' for r in requests)


def test_customer_identity_never_survives_order_projection():
    row={'id':1,'status':4,'customer':{'phone':'PRIVATE'},'observation':'PRIVATE',
         'products':[{'product_id':'sku','quantity':1,'sale_price':'10','vat':'0.21','serial_numbers':['PRIVATE']}],
         'attachments':[{'url':'PRIVATE'}]}
    result=business.project('orders_fbe',row)
    assert 'PRIVATE' not in str(result)
    assert result['products'][0]['sale_price']=='10'


@pytest.mark.parametrize('response', [httpx.Response(302,headers={'location':'https://example.com'}),
    httpx.Response(200,json={'isError':True,'results':[]}),httpx.Response(200,json={'isError':False})])
def test_failures_are_not_empty_complete_collections(response):
    with httpx.Client(transport=httpx.MockTransport(lambda r:response)) as client:
        with pytest.raises(ValueError):business.read_resource(client,None,'orders_fbe',{},delay=0)


def test_stock_mismatch_and_signed_invoice_amounts():
    summary=business.summarize({'offers':[{'id':1,'general_stock':2,'stock_2p_aging_bands':{'365+':3}}],
      'orders_fbe':[{'id':1,'status':4}], 'orders_seller':[], 'returns_fbe':[], 'returns_seller':[],
      'invoices':[{'category':'discount','currency':'RON','total_with_vat':'-2.50','is_storno':1}]})
    assert summary['inventory']['mismatched_skus']==1
    assert summary['inventory']['aging_total']==3
    assert summary['invoice_totals'][0]['amount_as_reported']=='-2.50'
    assert summary['purchase_cost_status']=='missing'


@pytest.mark.parametrize('result',[[],{'invoices':[]},{'total_results':True,'invoices':[]},
    {'total_results':-1,'invoices':[]}])
def test_invoice_requires_documented_count(result):
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'isError':False,'results':result}))) as client:
        with pytest.raises(ValueError):business.read_resource(client,None,'invoices',{},delay=0)


def test_missing_inventory_is_unknown_not_zero():
    data={'offers':[{'id':1}],'orders_fbe':[],'orders_seller':[],'returns_fbe':[], 'returns_seller':[],'invoices':[]}
    inventory=business.summarize(data)['inventory']
    assert inventory['general_stock_total'] is None and inventory['aging_total'] is None
    assert inventory['stock_rows_unknown']==1 and inventory['aging_rows_unknown']==1
