"""Explicit single-offer price writes; independent of local-only issue approvals."""
import hashlib
import json
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import settings
from app.services import store_artifacts as artifacts

BASE = 'https://marketplace-api.emag.ro/api-3/'
CORE = ('store_id', 'snapshot_id', 'source', 'product_id', 'before', 'after', 'price_basis')
UNRESOLVED = ('submitting', 'uncertain', 'submitted_unverified')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(p):
    return hashlib.sha256(_json({k: p[k] for k in CORE}).encode()).hexdigest()


def _text(value, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError('A nonempty bounded text value is required')
    return value.strip()


def _id(value):
    if type(value) not in (str, int) or not re.fullmatch(r'[1-9][0-9]{0,15}', str(value)):
        raise ValueError('A canonical positive offer ID is required')
    if int(value) > 9007199254740991:
        raise ValueError('Offer ID exceeds exact JSON integer range')
    return str(value)


def _amount(value, *, zero=False):
    if type(value) not in (str, int, float):
        raise ValueError('Price must be a finite number')
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or (not zero and n == 0) or n > 1000000000:
            raise ValueError('Price outside supported range')
        if n != n.quantize(Decimal('0.0001')):
            raise ValueError('Price supports at most four decimal places')
    except InvalidOperation:
        raise ValueError('Invalid price') from None
    return format(n.normalize(), 'f')


def _baseline(offer):
    if offer.get('currency') != 'RON':
        raise ValueError('Only explicit RON offers are supported')
    result = {'id': _id(offer.get('id')), 'part_number': _text(offer.get('part_number')),
              'part_number_key': _text(offer.get('part_number_key')), 'currency': 'RON',
              'sale_price': _amount(offer.get('sale_price')),
              'min_sale_price': _amount(offer.get('min_sale_price'), zero=True),
              'max_sale_price': _amount(offer.get('max_sale_price'))}
    if Decimal(result['min_sale_price']) > Decimal(result['max_sale_price']):
        raise ValueError('Seller price bounds are inconsistent')
    return result


@contextmanager
def _db():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(settings.data_dir / 'emag-api-changes.sqlite3', timeout=15)
    try:
        db.execute('CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, store TEXT, product TEXT, state TEXT, payload TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS events (proposal TEXT, payload TEXT)')
        with db:
            yield db
    finally:
        db.close()


def _load(db, store, proposal_id):
    artifacts.validate_id(store)
    if not isinstance(proposal_id, str) or not re.fullmatch('[a-f0-9]{32}', proposal_id):
        raise ValueError('Invalid proposal ID')
    row = db.execute('SELECT payload,state,product FROM proposals WHERE store=? AND id=?', (store, proposal_id)).fetchone()
    if row is None:
        raise ValueError('Proposal not found in this store')
    p = json.loads(row[0])
    if (p['store_id'] != store or p['proposal_id'] != proposal_id or p['state'] != row[1]
            or p['product_id'] != row[2] or _digest(p) != p['digest']):
        raise ValueError('Proposal integrity check failed')
    return p


def _save(db, p, state, actor, **updates):
    event = {'state': state, 'actor': _text(actor), 'at': _now()}
    p.update(state=state, updated_at=event['at'], revision=p.get('revision', 0) + 1, **updates)
    p['history'] = (p.get('history', []) + [event])[-50:]
    db.execute('INSERT OR REPLACE INTO proposals VALUES (?,?,?,?,?)',
               (p['proposal_id'], p['store_id'], p['product_id'], state, _json(p)))
    db.execute('INSERT INTO events VALUES (?,?)', (p['proposal_id'], _json(event)))
    return p


def _current(p):
    s = artifacts.read_snapshot(p['store_id'])
    if (s['snapshot_id'] != p['snapshot_id'] or s['source'] != BASE
            or s['platform'] != 'emag' or s['marketplace'] != 'RO'):
        raise ValueError('Source evidence is stale or not the RO API')
    rows = [o for o in s['data']['offers'] if str(o.get('id')) == p['product_id']]
    if len(rows) != 1 or _baseline(rows[0]) != p['before']:
        raise ValueError('Source offer no longer matches the approved evidence')


def prepare(store_id, snapshot_id, product_id, changes, actor):
    artifacts.validate_id(store_id)
    product_id = _id(product_id)
    if not isinstance(changes, dict) or set(changes) != {'sale_price'}:
        raise ValueError('Only one sale_price change is supported; stock and content writes are not enabled')
    after = {'sale_price': _amount(changes['sale_price'])}
    with artifacts.snapshot_guard(), _db() as db:
        s = artifacts.read_snapshot(store_id)
        if s['snapshot_id'] != snapshot_id or s['platform'] != 'emag' or s['marketplace'] != 'RO' or s['source'] != BASE:
            raise ValueError('Use the latest RO API snapshot')
        offers = [o for o in s['data']['offers'] if str(o.get('id')) == product_id]
        if len(offers) != 1:
            raise ValueError('Select one offer from this snapshot')
        before = _baseline(offers[0])
        if after['sale_price'] == before['sale_price']:
            raise ValueError('No-op writes are not supported')
        if not Decimal(before['min_sale_price']) <= Decimal(after['sale_price']) <= Decimal(before['max_sale_price']):
            raise ValueError('New price is outside the observed seller bounds')
        p = {'proposal_id': secrets.token_hex(16), 'store_id': store_id, 'snapshot_id': snapshot_id,
             'source': BASE, 'product_id': product_id, 'before': before, 'after': after,
             'price_basis': 'exclusive_vat', 'created_at': _now(), 'saleability_verified': False,
             'marketplace_write_attempted': False, 'submission_status': 'not_sent'}
        p['digest'] = _digest(p)
        return _save(db, p, 'prepared', actor)


def approve(store_id, proposal_id, digest, note, actor):
    note = _text(note, 2000)
    with artifacts.snapshot_guard(), _db() as db:
        db.execute('BEGIN IMMEDIATE')
        p = _load(db, store_id, proposal_id)
        if p['state'] != 'prepared' or digest != p['digest']:
            raise ValueError('Approval requires the exact prepared proposal digest')
        _current(p)
        return _save(db, p, 'approved', actor, approval={'digest': digest, 'note': note, 'actor': _text(actor), 'at': _now()})


def _binding(store_id, *, write=True):
    if settings.emag_write_store_id != store_id or (write and not settings.emag_writes_enabled):
        raise ValueError('Marketplace execution is disabled or this store is not explicitly bound')


def listing(store_id):
    artifacts.validate_id(store_id)
    with _db() as db:
        ids = [r[0] for r in db.execute('SELECT id FROM proposals WHERE store=? ORDER BY rowid DESC LIMIT 100', (store_id,))]
        rows = [_load(db, store_id, key) for key in ids]
    return {'store_id': store_id, 'writes_enabled': settings.emag_writes_enabled and settings.emag_write_store_id == store_id,
            'supported_fields': ['sale_price'], 'price_basis': 'exclusive_vat', 'proposals': rows,
            'limitation': 'Price verification does not verify saleability. Uncertain writes are never resent.'}


def _read(client, auth, p):
    r = client.post(BASE + 'product_offer/read', json={'id': int(p['product_id']), 'currentPage': 1, 'itemsPerPage': 100},
                    auth=auth, follow_redirects=False)
    if not r.is_success:
        raise ValueError('Live read HTTP error')
    body = r.json()
    rows = body.get('results') if isinstance(body, dict) and body.get('isError') is False else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError('Live read API or identity error')
    baseline = _baseline(rows[0])
    for key in ('id', 'part_number', 'part_number_key', 'currency'):
        if baseline[key] != p['before'][key]:
            raise ValueError('Live read belongs to a different offer')
    status = rows[0].get('offer_validation_status')
    observed = {'sale_price': baseline['sale_price'], 'offer_validation_status': {
        'value': status.get('value') if isinstance(status, dict) and type(status.get('value')) is int else None},
        'captured_at': _now()}
    return baseline, observed


def _finish(store_id, proposal_id, state, actor, *, expected_revision=None, **updates):
    with _db() as db:
        db.execute('BEGIN IMMEDIATE')
        p = _load(db, store_id, proposal_id)
        if expected_revision is not None and p['revision'] != expected_revision:
            raise ValueError('Receipt changed during reconciliation; reload first')
        return _save(db, p, state, actor, **updates)


def execute(store_id, proposal_id, digest, confirmed, actor, client, auth):
    _binding(store_id)
    if type(confirmed) is not bool or not confirmed:
        raise ValueError('Explicit confirmation is required')
    with artifacts.snapshot_guard(), _db() as db:
        db.execute('BEGIN IMMEDIATE')
        p = _load(db, store_id, proposal_id)
        if p['state'] != 'approved' or digest != p['digest'] or p['approval']['digest'] != digest:
            raise ValueError('Only the exact approved proposal can be executed once')
        _current(p)
        other = db.execute('SELECT id FROM proposals WHERE store=? AND product=? AND state IN (?,?,?) AND id<>?',
                           (store_id, p['product_id'], *UNRESOLVED, proposal_id)).fetchone()
        if other:
            raise ValueError('Another attempt on this offer is unresolved; reconcile first')
        _save(db, p, 'submitting', actor, attempt_started_at=_now())
    try:
        before, _ = _read(client, auth, p)
        if before != p['before']:
            raise ValueError('Live offer changed')
        with artifacts.snapshot_guard():
            _current(p)
            _binding(store_id)
            _finish(store_id, proposal_id, 'submitting', actor, marketplace_write_attempted=True)
            # Exactly one POST, never an automatic retry. Reads/writes use fixed origins.
            response = client.post(BASE + 'offer/save',
                json={'data': [{'id': int(p['product_id']), 'sale_price': float(p['after']['sale_price'])}]},
                auth=auth, follow_redirects=False)
    except (httpx.HTTPError, ValueError):
        with _db() as db:
            current = _load(db, store_id, proposal_id)
        attempted = current['marketplace_write_attempted']
        return _finish(store_id, proposal_id, 'uncertain' if attempted else 'preflight_failed', actor,
                       submission_status='uncertain' if attempted else 'not_sent',
                       reason='write_delivery_unknown' if attempted else 'live_preflight_failed')

    receipt = {'http_status': response.status_code,
               'response_sha256': hashlib.sha256(response.content).hexdigest()}
    accepted = False
    try:
        body = response.json() if len(response.content) <= 1000000 else None
        accepted = response.is_success and isinstance(body, dict) and body.get('isError') is False
    except ValueError:
        pass
    observed = None
    try:
        _, observed = _read(client, auth, p)
    except (httpx.HTTPError, ValueError):
        pass
    matches = observed is not None and observed['sale_price'] == p['after']['sale_price']
    state = ('verified' if matches else 'submitted_unverified') if accepted else 'uncertain'
    return _finish(store_id, proposal_id, state, actor, receipt=receipt, observed=observed,
                   observed_price_matches=matches, submission_status='accepted' if accepted else 'uncertain')


def reconcile(store_id, proposal_id, actor, client, auth):
    _binding(store_id, write=False)
    with _db() as db:
        p = _load(db, store_id, proposal_id)
    if p['state'] not in UNRESOLVED:
        raise ValueError('Only an unresolved submission can be read back')
    # Do not race an active attempt. Crashed attempts remain conservative and never replayable.
    if p['state'] == 'submitting':
        age = datetime.now(timezone.utc) - datetime.fromisoformat(p['attempt_started_at'])
        if age.total_seconds() < 120:
            raise ValueError('Attempt may still be running; wait before reconciliation')
    try:
        _, observed = _read(client, auth, p)
    except (httpx.HTTPError, ValueError):
        return _finish(store_id, proposal_id, p['state'], actor, expected_revision=p['revision'],
                       reconciliation_reason='live_read_failed')
    matches = observed['sale_price'] == p['after']['sale_price']
    # Ambiguous delivery stays blocked even if today's value matches: do not infer acceptance.
    state = 'verified' if matches and p['submission_status'] == 'accepted' else p['state']
    return _finish(store_id, proposal_id, state, actor, expected_revision=p['revision'],
                   observed=observed, observed_price_matches=matches)


def live_execute(store_id, proposal_id, digest, confirmed, actor):
    _binding(store_id)
    from app.services.windows_credentials import read_emag_credentials
    auth = read_emag_credentials()
    # The default HTTP transport has zero retries and retains environment proxy routing.
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        return execute(store_id, proposal_id, digest, confirmed, actor, client, auth)


def live_reconcile(store_id, proposal_id, actor):
    _binding(store_id, write=False)
    from app.services.windows_credentials import read_emag_credentials
    auth = read_emag_credentials()
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        return reconcile(store_id, proposal_id, actor, client, auth)
