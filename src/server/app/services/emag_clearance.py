"""Deterministic stock-clearance observations; never prices, purchases or sales forecasts."""
from datetime import datetime, timedelta
from app.services import emag_operations, emag_audit

BANDS=('0-30','31-60','61-90','91-180','181-270','271-365','365+')
PRIORITIES={'restore_sales':0,'review_aged_stock':1,'consume_stock':2,'verify_stock':3,'zero_stock':4}


def known_stock(value):
    return type(value) is int and value>=0


def build(snapshot, previous=(), history_incomplete=False):
    offers=snapshot['data']['offers']
    issues=emag_operations._issues(snapshot)
    by_product={}
    for issue in issues:
        by_product.setdefault(str(issue['id']),[]).append({'issue_id':issue['issue_id'],'reason':issue['reason']})
    rows=[]
    for index,offer in enumerate(offers):
        stock=offer.get('general_stock');stock=stock if known_stock(stock) else None
        age=offer.get('stock_2p_aging_bands')
        age_valid=isinstance(age,dict) and set(age)==set(BANDS) and all(known_stock(v) for v in age.values())
        aging_status='unknown'
        if age_valid:
            aging_status='consistent' if stock is not None and sum(age.values())==stock else 'inconsistent' if stock is not None else 'unreconciled'
        aged=sum(age[k] for k in BANDS[4:]) if aging_status=='consistent' else None
        blockers=by_product.get(str(offer['id']),[])
        if stock is None:priority='verify_stock'
        elif stock==0:priority='zero_stock'
        elif blockers:priority='restore_sales'
        elif aged:priority='review_aged_stock'
        else:priority='consume_stock'
        rows.append({'offer_id':str(offer['id']),'name':offer.get('name'),'sku':offer.get('part_number'),
            'stock':stock,'aging_status':aging_status,'aged_181_plus':aged,
            'aged_365_plus':age['365+'] if aging_status=='consistent' else None,
            'priority':priority,'issues':blockers,'sale_price':offer.get('sale_price'),
            'source_refs':{'stock':f'/data/offers/{index}/general_stock','aging':f'/data/offers/{index}/stock_2p_aging_bands'}})
    rows.sort(key=lambda r:(PRIORITIES[r['priority']],-(r['aged_365_plus'] or 0),-(r['aged_181_plus'] or 0),-(r['stock'] or 0),r['offer_id']))
    known=[r['stock'] for r in rows if r['stock'] is not None]
    summary={'products':len(rows),'stock_known_total':sum(known) if known else None,
        'unknown_stock_products':sum(r['stock'] is None for r in rows),
        'blocked_with_stock_products':sum(r['priority']=='restore_sales' for r in rows),
        'blocked_with_stock_units':sum(r['stock'] for r in rows if r['priority']=='restore_sales'),
        'aged_181_plus_known':sum(r['aged_181_plus'] for r in rows if r['aged_181_plus'] is not None),
        'aging_inconsistent_products':sum(r['aging_status']=='inconsistent' for r in rows),
        'aging_unknown_products':sum(r['aging_status'] in ('unknown','unreconciled') for r in rows)}
    if not any(r['aged_181_plus'] is not None for r in rows):summary['aged_181_plus_known']=None
    cutoff=datetime.fromisoformat(snapshot['captured_at'].replace('Z','+00:00'))-timedelta(days=7)
    candidates=[old for old in previous if emag_audit._compatible(snapshot,old) and datetime.fromisoformat(old['captured_at'].replace('Z','+00:00'))<=cutoff]
    weekly={'status':'unavailable','net_decrease':None,'history_incomplete':history_incomplete}
    if candidates:
        baseline=max(candidates,key=lambda s:datetime.fromisoformat(s['captured_at'].replace('Z','+00:00')))
        before={str(o['id']):o.get('general_stock') for o in baseline['data']['offers']}
        after={str(o['id']):o.get('general_stock') for o in offers}
        matched=[key for key in before.keys() & after.keys() if known_stock(before[key]) and known_stock(after[key])]
        weekly.update(status='available' if matched else 'incomplete',baseline_snapshot_id=baseline['snapshot_id'],
            baseline_captured_at=baseline['captured_at'],matched_products=len(matched),
            net_decrease=sum(before[k]-after[k] for k in matched) if matched else None,
            not_observed_now=len(before.keys()-after.keys()),newly_observed=len(after.keys()-before.keys()))
    commercial=snapshot['data'].get('commercial_evidence',{})
    statuses={};resources=[];invalid=0;seen=set()
    if isinstance(commercial,dict):
        for resource in ('orders_fbe','orders_seller'):
            entries=commercial.get(resource)
            if not isinstance(entries,list):continue
            resources.append(resource)
            for order in entries:
                if not isinstance(order,dict) or order.get('id',order.get('emag_id')) is None:
                    invalid+=1;continue
                identity=(resource,str(order.get('id',order.get('emag_id'))))
                if identity in seen:
                    invalid+=1;continue
                seen.add(identity);status=str(order.get('status','unknown'))
                statuses[status]=statuses.get(status,0)+1
    else:invalid+=1
    commercial_summary=snapshot['data'].get('commercial_summary')
    window=commercial_summary.get('window') if isinstance(commercial_summary,dict) else None
    if not isinstance(window,dict) or not all(isinstance(window.get(key),str) for key in ('start','end')):
        window=None
    return {'store_id':snapshot['store_id'],'snapshot_id':snapshot['snapshot_id'],'captured_at':snapshot['captured_at'],
        'summary':summary,'rows':rows,'weekly_stock_change':weekly,
        'order_observations':{'resources':resources,'status_counts':statuses,'invalid_or_duplicate_records':invalid,
                              'verified_sales_units':None,'window':window},
        'limitations':['Tracked blockers are observations, not a full availability check.',
            'Only complete age bands reconciled to total stock affect aging priority.',
            'Stock decrease is not verified sales: returns, adjustments and transfers may change inventory.',
            'Order status semantics, costs and payment reconciliation are unverified; no recovery value, clearance price or sell-through forecast is computed.',
            'A weekly comparison uses the closest compatible scanned snapshot at least seven days earlier; its interval may exceed seven days.'],
        'marketplace_writes':False}


def render(result):
    summary=result['summary']
    positive=[row for row in result['rows'] if row['stock'] is not None and row['stock']>0]
    lines=['## Existing-stock clearance',
        f"Known stock: {summary['stock_known_total']}; stock unknown products: {summary['unknown_stock_products']}.",
        f"Tracked blockers with stock: {summary['blocked_with_stock_products']} products / {summary['blocked_with_stock_units']} units.",
        f"Reconciled 181+ day units: {summary['aged_181_plus_known']}; aging mismatches: {summary['aging_inconsistent_products']} products.",
        'Stock movement is not verified sales or recovered cash. No procurement, automatic markdown or marketplace writes.',
        'Positive-stock priorities (first 50):','| Product | SKU | Stock | Priority | 181+ units |', '|---|---|---|---|---|']
    for row in positive[:50]:
        lines.append('| '+' | '.join(emag_audit._cell(value,100) for value in
            (row['offer_id'],row['sku'],row['stock'],row['priority'],row['aged_181_plus']))+' |')
    lines.append(f'Priority table truncated: {len(positive)>50}. Inspect the snapshot-bound workbench for full field references.')
    return '\n'.join(lines)
