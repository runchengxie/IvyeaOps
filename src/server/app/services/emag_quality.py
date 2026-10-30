"""Bounded return observations and conservative Listing claim review hints."""
import re


def return_voc(snapshot):
    data=snapshot['data']; evidence=data.get('commercial_evidence',{})
    groups={};seen=set();missing=0;unmatched=0;invalid=0
    if not isinstance(evidence,dict):
        evidence={};invalid=1
    available=[key for key in ('returns_fbe','returns_seller') if isinstance(evidence.get(key),list)]
    offers=data.get('offers',[])
    for resource in available:
        for index,case in enumerate(evidence[resource]):
            if not isinstance(case,dict) or not isinstance(case.get('products'),list):
                invalid+=1;continue
            case_id=case.get('id',case.get('emag_id'))
            if case_id is None:
                invalid+=1;continue
            for line_index,line in enumerate(case['products']):
                if not isinstance(line,dict):
                    invalid+=1;continue
                reason=line.get('return_reason')
                if not isinstance(reason,str) or not reason.strip():
                    missing+=1;continue
                if line.get('product_id') is not None:
                    candidates=[o for o in offers if str(o['id'])==str(line['product_id'])
                        and (not line.get('part_number') or o.get('part_number')==line['part_number'])]
                else:
                    candidates=[o for o in offers if line.get('part_number') and o.get('part_number')==line['part_number']]
                if len(candidates)!=1:
                    unmatched+=1;continue
                product=str(candidates[0]['id']);normalized=' '.join(reason.split())[:256]
                identity=(resource,str(case_id),product,normalized.casefold())
                if identity in seen:continue
                seen.add(identity)
                key=(product,normalized.casefold())
                group=groups.setdefault(key,{'offer_id':product,'reason':normalized,'case_count':0,'source_refs':[]})
                group['case_count']+=1
                if len(group['source_refs'])<10:
                    group['source_refs'].append(f'/data/commercial_evidence/{resource}/{index}/products/{line_index}/return_reason')
    ordered=sorted(groups.values(),key=lambda g:(-g['case_count'],g['offer_id'],g['reason']))
    return {'snapshot_id':snapshot['snapshot_id'],'scope':'captured_return_requests_only',
        'status':'unavailable' if not available else 'partial' if len(available)<2 or invalid else 'available',
        'resources':available,'groups':ordered[:100],'groups_truncated':len(ordered)>100,
        'missing_reason_rows':missing,'unmatched_rows':unmatched,'invalid_rows':invalid,
        'limitation':'Request cases are not completed refunds, review samples or overall customer satisfaction. Reasons are grouped as reported, not inferred root causes.'}


def listing_check(title, body, offer):
    patterns=(r'\bIP\d{2}\b',r'\b(?:waterproof|certified|medical|antibacterial|FDA|CE)\b',
              r'\b\d+(?:[.,]\d+)?\s*(?:ml|litres?|cm|mm|kg|watts?)\b',r'防水|认证|医用|抗菌|\d+(?:毫升|厘米|公斤)')
    flags=[]
    for field,text in (('title',title),('body',body)):
        for pattern in patterns:
            for match in re.finditer(pattern,text,re.IGNORECASE):
                if len(flags)>=50:break
                flags.append({'claim':match.group(0),'field':field,'offset':match.start(),
                              'reason':'Independent product evidence required; a captured offer title does not verify this claim.'})
    return {'offer_id':str(offer['id']),'requires_review':bool(flags),'flags':flags,
            'compliance_verified':False,'limitation':'Conservative multilingual pattern hints only; unflagged text is not certified factual or platform-compliant. Images are not inspected.'}
