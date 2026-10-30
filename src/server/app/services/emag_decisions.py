"""Deterministic issue diagnostics and fail-closed field-level decision gates."""
import json
from app.core.findings import Evidence, Finding, Action
from app.services import emag_operations

REVIEW_DETAIL = 'Review platform evidence and record a local proposal.'


def diagnose(snapshot, issue_id=None):
    issues = emag_operations._issues(snapshot)
    if issue_id is not None:
        issues = [issue for issue in issues if issue['issue_id']==issue_id]
    rows = snapshot['data']['offers']
    findings = []
    for issue in issues[:100]:
        index = next(i for i, row in enumerate(rows) if row['id'] == issue['id'])
        row = rows[index]
        identity = {'store_id':snapshot['store_id'], 'offer_id':str(row['id']), 'snapshot_id':snapshot['snapshot_id']}
        common = {**identity, 'source_ref':snapshot['snapshot_id'], 'source':snapshot['source'],
                  'as_of':snapshot['captured_at'], 'target':str(row['id'])}
        status = 'offer_validation_status' if issue['reason']=='invalid_price' else 'validation_status'
        evidence = []
        for key in (status, 'general_stock'):
            value = row.get(key)
            missing = value is None or (key=='general_stock' and (type(value) is not int or value<0))
            evidence.append(Evidence(**common, evidence_id=key, metric=key, value=None if missing else value,
                evidence_type='missing' if missing else 'observed', field_path=f'/data/offers/{index}/{key}',
                missing_reason='Field absent or invalid in captured evidence' if missing else ''))
        evidence.append(Evidence(**common,evidence_id='diagnosis',metric='issue_reason',value=issue['reason'],
            evidence_type='inference',derived_from=[status],note='Deterministic existing eMAG status rule; not a confirmed root cause.'))
        findings.append(Finding(**identity,id=issue['issue_id'],title=issue['reason'],
            reasoning='Inspect the retained platform status before proposing a marketplace change.',evidence=evidence,
            actions=[Action(type='review',target=str(row['id']),detail=REVIEW_DETAIL,
                guardrail='Current snapshot, same store/product and verified field dependencies required.',required_evidence=['diagnosis'])]).model_dump())
    return {'schema_version':1,'store_id':snapshot['store_id'],'snapshot_id':snapshot['snapshot_id'],
            'findings':findings,'findings_truncated':len(issues)>100,'model_used':False,'marketplace_writes':False}


def _resolve(snapshot, path, offer_id, allow_absent=False):
    parts = path.split('/')
    if len(parts)!=5 or parts[:3]!=['','data','offers'] or not parts[3].isdigit():
        raise ValueError('Evidence must point to a product field')
    rows = snapshot['data']['offers']
    index = int(parts[3])
    if index>=len(rows) or str(rows[index]['id'])!=offer_id:
        raise ValueError('Field belongs to a different product')
    if parts[4] not in rows[index]:
        if allow_absent:
            return None
        raise ValueError('Observed field is absent')
    return rows[index][parts[4]]


def verify(raw, snapshot):
    errors = []
    try:
        finding = Finding.model_validate(raw)
        identity = (snapshot['store_id'],snapshot['snapshot_id'],finding.offer_id)
        if (finding.store_id,finding.snapshot_id,finding.offer_id)!=identity or not finding.offer_id:
            raise ValueError('Finding entity or source version mismatch')
        issue = next((i for i in emag_operations._issues(snapshot) if i['issue_id']==finding.id and str(i['id'])==finding.offer_id),None)
        if issue is None:
            raise ValueError('Finding is not an observed issue in this snapshot')
        seen = {}
        supported = {}
        for e in finding.evidence:
            if not e.evidence_id or e.evidence_id in seen:
                raise ValueError('Evidence IDs must be present and unique')
            if ((e.store_id,e.snapshot_id,e.offer_id)!=identity or e.source_ref!=snapshot['snapshot_id']
                    or e.source!=snapshot['source'] or e.as_of!=snapshot['captured_at']):
                raise ValueError('Evidence entity/source version mismatch')
            if e.evidence_type in ('observed','missing') and (e.evidence_id!=e.metric or not e.field_path.endswith('/'+e.metric)):
                raise ValueError('Field identity does not match evidence metric')
            if e.evidence_type=='observed':
                actual = _resolve(snapshot,e.field_path,e.offer_id)
                if json.dumps(actual,sort_keys=True,allow_nan=False)!=json.dumps(e.value,sort_keys=True,allow_nan=False):
                    raise ValueError('Observed value differs from snapshot field')
                if e.metric=='general_stock' and (type(actual) is not int or actual<0):
                    raise ValueError('Invalid stock cannot be labelled observed')
                if actual is None:
                    raise ValueError('Null is missing, not observed')
                supported[e.evidence_id] = True
            elif e.evidence_type=='missing':
                if e.value is not None or not e.missing_reason:
                    raise ValueError('Missing evidence requires null value and a reason')
                actual = _resolve(snapshot,e.field_path,e.offer_id,allow_absent=True)
                if actual is not None and not (e.metric=='general_stock' and (type(actual) is not int or actual<0)):
                    raise ValueError('Missing label contradicts captured field')
                supported[e.evidence_id] = False
            elif e.evidence_type=='inference':
                status = 'offer_validation_status' if issue['reason']=='invalid_price' else 'validation_status'
                if e.evidence_id!='diagnosis' or e.metric!='issue_reason' or e.value!=issue['reason'] or e.derived_from!=[status]:
                    raise ValueError('Unsupported inference rule')
                if any(ref not in seen for ref in e.derived_from):
                    raise ValueError('Missing or cyclic evidence dependency')
                supported[e.evidence_id] = all(supported[ref] for ref in e.derived_from)
            else:
                raise ValueError('Derived/estimate values need a registered verifier before decision use')
            seen[e.evidence_id] = e
        if not finding.actions:
            raise ValueError('No bounded review action')
        for action in finding.actions:
            if (action.type!='review' or action.target!=finding.offer_id
                    or action.required_evidence!=['diagnosis'] or action.detail!=REVIEW_DETAIL):
                raise ValueError('Only source-bound review actions are supported')
            if not all(supported.get(ref,False) for ref in action.required_evidence):
                raise ValueError('Action depends on missing or unsupported evidence')
    except (ValueError,KeyError,TypeError) as exc:
        errors.append(str(exc))
    return {'valid':not errors,'errors':errors,'marketplace_writes':False}
