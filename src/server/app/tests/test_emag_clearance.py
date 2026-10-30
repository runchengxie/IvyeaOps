from app.services import emag_clearance as service


def snap(rows,at='2026-10-30T00:00:00Z',sid='current'):
    return {'store_id':'demo-ro','snapshot_id':sid,'platform':'emag','marketplace':'RO','source':'synthetic',
            'coverage':['offers'],'limitations':['test'],'captured_at':at,'data':{'offers':rows}}


def bands(old=0,new=0):
    return {'0-30':new,'31-60':0,'61-90':0,'91-180':0,'181-270':0,'271-365':0,'365+':old}


def test_prioritizes_blocked_stock_then_confirmed_aging():
    data=snap([{'id':1,'general_stock':5,'stock_2p_aging_bands':bands(5)},
               {'id':2,'general_stock':1,'offer_validation_status':{'value':2},'stock_2p_aging_bands':bands(0,1)},
               {'id':3,'general_stock':0},{'id':4}])
    result=service.build(data)
    assert [r['offer_id'] for r in result['rows']]==['2','1','4','3']
    assert result['rows'][0]['priority']=='restore_sales'
    assert result['rows'][1]['aged_181_plus']==5
    assert result['rows'][0]['source_refs']['stock']=='/data/offers/1/general_stock'
    assert result['summary']['stock_known_total']==6
    assert result['summary']['unknown_stock_products']==1


def test_mismatched_or_missing_age_is_not_trusted_for_ranking():
    result=service.build(snap([{'id':1,'general_stock':2,'stock_2p_aging_bands':bands(5)},
                               {'id':2,'general_stock':3}]))
    assert all(r['aged_181_plus'] is None for r in result['rows'])
    assert result['summary']['aging_inconsistent_products']==1
    assert result['summary']['aging_unknown_products']==1


def test_weekly_change_does_not_turn_missing_products_into_sales():
    current=snap([{'id':1,'general_stock':3},{'id':3,'general_stock':2}])
    old=snap([{'id':1,'general_stock':5},{'id':2,'general_stock':20}],at='2026-10-22T00:00:00Z',sid='old')
    result=service.build(current,[old])['weekly_stock_change']
    assert result['net_decrease']==2 and result['matched_products']==1
    assert result['not_observed_now']==1 and result['newly_observed']==1
    assert service.build(current)['weekly_stock_change']['status']=='unavailable'


def test_unknown_stock_is_not_zero_and_orders_are_not_verified_sales():
    data=snap([{'id':1,'general_stock':True},{'id':2,'general_stock':-1},{'id':3,'general_stock':'3'}])
    data['data']['commercial_evidence']={'orders_fbe':[{'id':1,'status':0,'products':[{'product_id':1,'quantity':2}]}]}
    result=service.build(data)
    assert result['summary']['stock_known_total'] is None
    assert result['order_observations']['verified_sales_units'] is None
    assert result['order_observations']['status_counts']=={'0':1}


def test_malformed_optional_commercial_summary_keeps_clearance_available():
    for summary in (None,[],True,{'window':[]},{'window':{'start':123,'end':'bad'}}):
        data=snap([{'id':1,'general_stock':3}])
        data['data']['commercial_summary']=summary
        result=service.build(data)
        assert result['summary']['stock_known_total']==3
        assert result['order_observations']['window'] is None


def test_foreign_future_and_recent_snapshots_do_not_supply_weekly_baseline():
    current=snap([{'id':1,'general_stock':3}])
    foreign=snap([{'id':1,'general_stock':99}],at='2026-10-20T00:00:00Z');foreign['source']='other'
    future=snap([{'id':1,'general_stock':99}],at='2026-11-01T00:00:00Z')
    recent=snap([{'id':1,'general_stock':99}],at='2026-10-29T00:00:00Z')
    assert service.build(current,[foreign,future,recent])['weekly_stock_change']['status']=='unavailable'


def test_malformed_optional_orders_are_quarantined():
    current=snap([{'id':1,'general_stock':3}]);current['data']['commercial_evidence']={'orders_fbe':[None,{'products':[]}]}
    result=service.build(current)
    assert result['order_observations']['invalid_or_duplicate_records']==2
    assert result['summary']['stock_known_total']==3
