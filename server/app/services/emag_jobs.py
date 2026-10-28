"""Serialized manual read-only audits with immutable source/report references."""
import secrets
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from app.services import store_artifacts as artifacts, emag_operations, emag_business


def _root(store_id):
    return artifacts._root() / 'jobs' / artifacts.validate_id(store_id)


def latest(store_id):
    import json
    return json.loads((_root(store_id) / 'latest.json').read_text('utf-8'))


def compare(before, after):
    def index(rows):
        result = {str(row['id']): row for row in rows}
        if len(result) != len(rows):
            raise ValueError('Duplicate product IDs')
        return result
    def normalized(value):
        if value is None: return None
        try:
            number = Decimal(str(value))
            return number if number.is_finite() else str(value)
        except InvalidOperation:
            return str(value)
    old, new = index(before), index(after)
    result = []
    for key in sorted(old.keys() | new.keys()):
        if key not in old or key not in new:
            result.append(dict(id=key, field='observed_product', before=key in old, after=key in new))
            continue
        for field in ('sale_price','general_stock','offer_validation_status','validation_status'):
            a,b = old[key].get(field),new[key].get(field)
            equal = normalized(a) == normalized(b) if field in ('sale_price','general_stock') else a == b
            if not equal: result.append(dict(id=key,field=field,before=a,after=b))
    return result


def run(store_id, collect_fn=None):
    root = _root(store_id)
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / 'run-lock.sqlite3', timeout=0)
    try:
        # Fail before collecting if another process holds this store's lock.
        conn.execute('BEGIN IMMEDIATE')
        receipt = dict(run_id=secrets.token_hex(16),store_id=store_id,
                       started_at=datetime.now(timezone.utc).isoformat(),
                       mode='fresh_collection' if collect_fn else 'existing_snapshot',stage='source',status='running')
        try:
            try: previous = artifacts.read_snapshot(store_id)
            except FileNotFoundError: previous = None
            if collect_fn:
                receipt['stage']='collection'
                snapshot=emag_business.publish(store_id,collect_fn())
            elif previous:
                snapshot=previous
            else:
                raise FileNotFoundError('Collect evidence first')
            receipt['snapshot_id']=snapshot['snapshot_id']
            issues=emag_operations._issues(snapshot)
            receipt['stage']='report'
            delta = compare(previous['data']['offers'],snapshot['data']['offers']) if collect_fn and previous else []
            receipt['baseline_snapshot_id']=previous['snapshot_id'] if collect_fn and previous else None
            receipt['delta_available']=bool(collect_fn and previous)
            receipt['change_count']=len(delta)
            # Two individually valid snapshots can produce a delta larger than
            # either source. Keep a bounded preview; full evidence stays in the
            # immutable baseline/current snapshots referenced by the receipt.
            preview=[]
            for change in delta[:200]:
                if len(json.dumps(preview+[change],ensure_ascii=False).encode('utf-8'))>64000:
                    break
                preview.append(change)
            receipt['changes']=preview
            receipt['changes_truncated']=len(preview)!=len(delta)
            text = '\n'.join(['# eMAG manual audit',f"Source: {snapshot['snapshot_id']}",
                f"Captured: {snapshot['captured_at']}",f"Mode: {receipt['mode']}",
                f"Offers: {len(snapshot['data']['offers'])}; issue reasons: {len(issues)}",
                f"Observed field changes: {len(delta)} (baseline available: {receipt['delta_available']})",
                'Missing stock is unknown, not zero. Missing products are observations, not confirmed delistings.',
                'No marketplace writes. Costs must be supplied before pricing/profit decisions.',
                '## Issue references (first 200)',
                *[f"- Product {str(i['id'])[:100]}: {i['reason']}" for i in issues[:200]],
                f"Issue references truncated: {len(issues)>200}",
                '## Change preview',json.dumps(preview,ensure_ascii=False),
                f"Change preview truncated: {receipt['changes_truncated']}; compare the referenced source snapshots for complete evidence.",
                '## Source limitations',*['- '+str(x) for x in snapshot['limitations']]])
            report=artifacts.save_report(store_id,snapshot['snapshot_id'],'eMAG manual audit',text)
            receipt.update(report_id=report['report_id'],status='complete',stage='complete')
        except Exception as exc:
            # Never persist exception text: HTTP errors may contain credential-bearing URLs/payloads.
            receipt.update(status='failed',error_type=type(exc).__name__)
        receipt['finished_at']=datetime.now(timezone.utc).isoformat()
        artifacts._write_new(root / (receipt['run_id']+'.json'),receipt)
        artifacts._write_new(root / 'latest.json',receipt)
        conn.commit()
        return receipt
    finally:
        conn.close()
