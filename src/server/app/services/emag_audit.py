"""Bounded, source-labelled issue evidence for manual audit reports."""
from datetime import datetime
from html import escape
import re

from app.services import emag_operations, store_artifacts

HISTORY_LIMIT = 50
ISSUE_LIMIT = 100


def _compatible(current, other):
    return (other.get('store_id') == current['store_id']
            and other.get('platform') == current['platform']
            and other.get('marketplace') == current['marketplace']
            and other.get('source') == current['source']
            and set(other.get('coverage', [])) == set(current['coverage'])
            and datetime.fromisoformat(other['captured_at']) <= datetime.fromisoformat(current['captured_at']))


def history(snapshot):
    directory = store_artifacts._root() / 'snapshots' / store_artifacts.validate_id(snapshot['store_id'])
    files = sorted((p for p in directory.glob('*.json') if p.stem < snapshot['snapshot_id']), reverse=True)
    incomplete = len(files) > HISTORY_LIMIT
    result = []
    for path in files[:HISTORY_LIMIT]:
        try:
            item = store_artifacts.read_snapshot(snapshot['store_id'], path.stem)
            if _compatible(snapshot, item):
                emag_operations._issues(item)
                result.append(item)
        except (OSError, ValueError, KeyError, TypeError):
            incomplete = True
    return result, incomplete


def _cell(value, limit=160):
    text = ' '.join(str(value if value is not None else 'unknown').split())[:limit]
    text = escape(text).replace('|', '&#124;')
    return re.sub(r'([\\`*_\[\]()!])', r'\\\1', text)[:limit]


def _reason(issue):
    status = issue.get('platform_status')
    statuses = status if isinstance(status, list) else [status]
    messages = []
    for entry in statuses:
        if not isinstance(entry, dict):
            continue
        details = entry.get('error_details')
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    pieces = [detail.get(key) for key in ('message', 'extra_info') if isinstance(detail.get(key), str)]
                    if pieces:
                        messages.append(' — '.join(pieces))
        if not messages and isinstance(entry.get('errors'), str):
            messages.append(entry['errors'])
    return '; '.join(messages) if messages else 'Platform detail unavailable'


def render_issues(snapshot, previous_snapshots, baseline, *, history_incomplete):
    issues = emag_operations._issues(snapshot)
    first_seen = {(str(i['id']), i['reason']): snapshot['captured_at'] for i in issues}
    for old in previous_snapshots:
        if not _compatible(snapshot, old):
            continue
        for issue in emag_operations._issues(old):
            key = (str(issue['id']), issue['reason'])
            if key in first_seen and datetime.fromisoformat(old['captured_at']) < datetime.fromisoformat(first_seen[key]):
                first_seen[key] = old['captured_at']
    baseline_issues = None
    missing = []
    if baseline and _compatible(snapshot, baseline):
        old_issues = emag_operations._issues(baseline)
        baseline_issues = {(str(i['id']), i['reason']) for i in old_issues}
        current_keys = {(str(i['id']), i['reason']) for i in issues}
        missing = [i for i in old_issues if (str(i['id']), i['reason']) not in current_keys]
    lines = ['## Issue details',
             f"Store: {_cell(snapshot['store_id'])}; first observed means earliest matching captured time in the current and up to {HISTORY_LIMIT} previous imported snapshots, not when an issue began.",
             f'History scan incomplete: {history_incomplete}. Only matching source and coverage are compared.',
             'Baseline unavailable.' if baseline_issues is None else f"Baseline snapshot: {_cell(baseline['snapshot_id'])}.",
             'A missing baseline observation does not prove the issue is new or resolved.',
             'Platform evidence is a shortened preview; inspect the referenced snapshot for all retained details.',
             '',
             '| Product ID | SKU | Issue | Stock | Platform evidence preview | First observed in scanned history | Baseline |',
             '|---|---|---|---|---|---|---|']
    for issue in issues[:ISSUE_LIMIT]:
        key = (str(issue['id']), issue['reason'])
        state = 'baseline unavailable' if baseline_issues is None else ('observed in baseline' if key in baseline_issues else 'not observed in baseline')
        cells = (issue['id'], issue.get('part_number'), issue['reason'], issue.get('general_stock'),
                 _reason(issue), first_seen[key], state)
        limits = (80, 80, 50, 35, 160, 50, 40)
        lines.append('| ' + ' | '.join(_cell(value, limit) for value, limit in zip(cells, limits)) + ' |')
    if not issues:
        lines.append('| — | — | No tracked issues observed | — | — | — | — |')
    lines.append('')
    lines.append(f'Issue details truncated: {len(issues) > ISSUE_LIMIT}; total issue records: {len(issues)}.')
    if baseline_issues is not None:
        lines.append('## Baseline issues not observed in current snapshot')
        lines.append('This does not establish resolution; products or fields may be missing or unknown.')
        for issue in missing[:50]:
            lines.append(f"- Product {_cell(issue['id'], 80)}; SKU {_cell(issue.get('part_number'), 80)}; {_cell(issue['reason'], 50)}")
        lines.append(f'Baseline omissions truncated: {len(missing) > 50}; total not observed: {len(missing)}.')
    return '\n'.join(lines)
