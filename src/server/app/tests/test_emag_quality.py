from app.services import emag_quality as quality


def test_return_voc_deduplicates_cases_and_keeps_unknowns():
    snapshot={'snapshot_id':'s1','captured_at':'2026-10-30T00:00:00Z','data':{'offers':[{'id':1,'part_number':'SKU'}],
        'commercial_evidence':{'returns_fbe':[{'id':10,'products':[{'product_id':1,'return_reason':'Size mismatch'},{'product_id':1,'return_reason':'Size mismatch'}]},
                                            {'id':11,'products':[{'product_id':1}]}],'returns_seller':[]}}}
    result=quality.return_voc(snapshot)
    assert result['groups'][0]['case_count']==1
    assert result['missing_reason_rows']==1
    assert result['groups'][0]['source_refs'][0].endswith('/return_reason')
    assert result['scope']=='captured_return_requests_only'


def test_missing_return_resources_are_not_zero_returns():
    result=quality.return_voc({'snapshot_id':'s','data':{'offers':[]}})
    assert result['status']=='unavailable' and result['groups']==[]


def test_listing_claims_are_warnings_not_compliance_certification():
    result=quality.listing_check('IP68 certified','Waterproof medical 500ml',{'id':1,'name':'Example bottle'})
    assert result['requires_review'] is True
    assert any('IP68' in flag['claim'] for flag in result['flags'])
    assert quality.listing_check('Bottle','Plain description',{'id':1})['compliance_verified'] is False


def test_conflicting_return_identifiers_are_quarantined():
    snap={'snapshot_id':'s','data':{'offers':[{'id':1,'part_number':'SKU-A'}],
        'commercial_evidence':{'returns_fbe':[{'id':1,'products':[{'product_id':99,'part_number':'SKU-A','return_reason':'Wrong item'}]}],'returns_seller':[]}}}
    result=quality.return_voc(snap)
    assert result['groups']==[] and result['unmatched_rows']==1


def test_malformed_optional_returns_do_not_hide_workspace():
    for value in (None,[],True):
        result=quality.return_voc({'snapshot_id':'s','data':{'offers':[],'commercial_evidence':value}})
        assert result['status']=='unavailable' and result['invalid_rows']>=1
