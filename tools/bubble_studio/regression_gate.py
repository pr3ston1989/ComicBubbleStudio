"""Exact output regression gate, with explicitly reviewed geometry exceptions."""
import argparse
import json
import math
import copy
import hashlib
from pathlib import Path


def frozen_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def compare_context_change(before,after,rule):
    """An external visual policy binds whole results, never the model's claims."""
    errors=[];audit=after.get('analysis',{}).get('page_context',{});snapshot=audit.get('original',{})
    if before.get('lab',{}).get('sha256')!=rule.get('image_sha256'):errors.append('Different reviewed image')
    if frozen_digest(before['result'])!=rule.get('baseline_result_sha256'):errors.append('Different reviewed baseline')
    if frozen_digest(after['result'])!=rule.get('approved_result_sha256'):errors.append('Unreviewed context result')
    if (audit.get('status')!='applied' or snapshot.get('result')!=before['result']
        or snapshot.get('analysis',{}).get('reading_anchors')!=before.get('analysis',{}).get('reading_anchors')):
        errors.append('Missing independently verified reversible snapshot')
    if not rule.get('visual_review') or not rule.get('reason'):errors.append('Missing external visual review')
    if after.get('review',{}).get('verified') is not False:errors.append('Context page falsely marked verified')
    return errors


def contour_extension(before,after,width,height,rule):
    """Raster comparison preserves the old body independently of model claims."""
    import cv2
    import numpy as np
    try:
        for region in (before,after):
            if not region.get('polygons'):return 'missing contour'
            for key in ('x','y','w','h'):
                if not math.isfinite(region[key]):return 'invalid geometry'
            if region['w']<=0 or region['h']<=0:return 'empty geometry'
            if region['x']<0 or region['y']<0 or region['x']+region['w']>1.000001 or region['y']+region['h']>1.000001:
                return 'geometry outside page'
            for poly in region['polygons']:
                if len(poly)<3 or any(not math.isfinite(p[k]) or not 0<=p[k]<=1 for p in poly for k in ('x','y')):
                    return 'invalid contour'
        x=math.floor(min(before['x'],after['x'])*width)
        y=math.floor(min(before['y'],after['y'])*height)
        right=math.ceil(max(before['x']+before['w'],after['x']+after['w'])*width)
        bottom=math.ceil(max(before['y']+before['h'],after['y']+after['h'])*height)
        masks=[]
        for region in (before,after):
            mask=np.zeros((bottom-y+1,right-x+1),np.uint8)
            contours=[np.rint([[(region['x']+p['x']*region['w'])*width-x,
                               (region['y']+p['y']*region['h'])*height-y] for p in poly]).astype(np.int32)
                      for poly in region['polygons']]
            cv2.fillPoly(mask,contours,1);masks.append(mask>0)
        old,new=masks;count=np.count_nonzero(old)
        preserved=np.count_nonzero(old&new)/max(1,count)
        growth=np.count_nonzero(new&~old)/max(1,count)
        if preserved<rule.get('min_mask_preserved',.995):return 'old contour pixels lost'
        if not rule.get('min_mask_growth',.03)<=growth<=rule.get('max_mask_growth',.20):return 'unexpected contour growth'
    except (ValueError,TypeError,KeyError,OverflowError):
        return 'invalid contour evidence'
    return None


def compare_text_splits(before, after, rule):
    """Approve only reviewed replacement rectangles, preserving other objects.

    The baseline's spatial OCR is independent of the candidate's split audit.
    A self-reported successful split never authorizes missing or cropped words.
    """
    errors=[];a,b=before['result'],after['result']
    old={r['id']:r for r in a['bubbles']};new={r['id']:r for r in b['bubbles']}
    preserved=rule['preserved_regions'];splits=rule['splits']
    old_used=list(preserved)+[s['old_region'] for s in splits]
    new_used=list(preserved.values())+[r['id'] for s in splits for r in s['new_regions']]
    if (len(set(old_used))!=len(old_used) or set(old_used)!=set(old)
            or len(set(new_used))!=len(new_used) or set(new_used)!=set(new)):
        return ['Incomplete or duplicated split mapping']
    if {k:v for k,v in a.items() if k not in {'bubbles','confidence'}}!={k:v for k,v in b.items() if k not in {'bubbles','confidence'}}:
        errors.append('Page metadata or panels changed during split')
    if any(r['id']!=f'b{i+1}' or r['order']!=i+1 for i,r in enumerate(b['bubbles'])):
        errors.append('Invalid split reading-order metadata')
    if 'confidence' in b and not math.isclose(b['confidence'],sum(r['confidence'] for r in b['bubbles'])/max(1,len(b['bubbles'])),abs_tol=1e-12):
        errors.append('Invalid aggregate split confidence')
    for old_id,new_id in preserved.items():
        if {k:v for k,v in old[old_id].items() if k not in {'id','order'}}!={k:v for k,v in new[new_id].items() if k not in {'id','order'}}:
            errors.append('Protected region changed during split: '+old_id)
    for split in splits:
        parent=old[split['old_region']];targets=split['new_regions']
        if parent.get('type')!='text' or parent.get('polygons') or parent.get('polygon') or len(targets)<2:
            errors.append('Only a text rectangle may be split')
        for target in targets:
            if new[target['id']]!=target:errors.append('Unreviewed split geometry or order: '+target['id'])
            if (target.get('type')!='text' or target.get('polygons') or target.get('polygon')
                    or any(target.get(k)!=parent.get(k) for k in ('confidence','source','panel_id'))):
                errors.append('Split altered classification, confidence, source or panel')
            if (any(not math.isfinite(target[k]) for k in ('x','y','w','h')) or min(target['w'],target['h'])<=0
                    or min(target['x'],target['y'])<0 or target['x']+target['w']>1.000001 or target['y']+target['h']>1.000001):
                errors.append('Invalid split coordinates')
        for i,x in enumerate(targets):
            for y in targets[i+1:]:
                if min(x['x']+x['w'],y['x']+y['w'])>max(x['x'],y['x']) and min(x['y']+x['h'],y['y']+y['h'])>max(x['y'],y['y']):
                    errors.append('Split rectangles overlap')
        check=next((r for r in before.get('analysis',{}).get('text_check',{}).get('regions',[]) if r['region_id']==parent['id']),None)
        if not check or len(check.get('ocr',[]))<4:
            errors.append('Missing baseline spatial OCR for text split');continue
        x1,y1,x2,y2=check['box'];width,height=a['width'],a['height']
        covered_counts=[0]*len(targets)
        for row in check['ocr']:
            if not row.get('box') or row.get('score',0)<.85:
                errors.append('Uncertain baseline OCR in split');continue
            u,v,w,z=row['box'];px1,py1=x1+u*(x2-x1),y1+v*(y2-y1);px2,py2=x1+w*(x2-x1),y1+z*(y2-y1)
            owners=[i for i,r in enumerate(targets) if r['x']*width<=px1+.1 and (r['x']+r['w'])*width>=px2-.1
                    and r['y']*height<=py1+.1 and (r['y']+r['h'])*height>=py2-.1]
            if len(owners)!=1:errors.append('Split lost or duplicated OCR line: '+row['text'])
            else:covered_counts[owners[0]]+=1
        if min(covered_counts)<2:errors.append('A split column has fewer than two confirmed lines')
    return errors


def compare_content_removals(before, after, rule):
    """Fixed reviewed removals; candidate claims cannot authorize deletions."""
    errors=[];a=before['result'];audit=after.get('analysis',{}).get('content_filter',{})
    removed=rule['removed_region_ids'];ids=[r['id'] for r in a['bubbles']]
    if not removed or len(set(removed))!=len(removed) or not set(removed)<=set(ids):
        return ['Invalid independently reviewed removal list']
    original={'result':a,'reading_anchors':before.get('analysis',{}).get('reading_anchors',{}),
              'text_check':before.get('analysis',{}).get('text_check'),'review':before['review']}
    if audit.get('original')!=original:errors.append('Pre-filter snapshot differs from independent baseline')
    if (audit.get('status')!='applied' or audit.get('kind')!=rule['kind']
            or audit.get('removed_region_ids')!=removed or not audit.get('evidence')):
        errors.append('Missing or inconsistent reversible filter audit')
    expected=copy.deepcopy(a);kept=[r for r in expected['bubbles'] if r['id'] not in removed]
    mapping={r['id']:f'b{i+1}' for i,r in enumerate(kept)}
    for i,r in enumerate(kept):r['id']=f'b{i+1}';r['order']=i+1
    expected['bubbles']=kept;expected['confidence']=sum(r['confidence'] for r in kept)/max(1,len(kept))
    if after['result']!=expected:errors.append('Protected geometry, panels, order or metadata changed during removal')
    if audit.get('preserved_id_mapping')!=mapping:errors.append('Invalid preserved ID mapping')
    anchors={mapping[k]:v for k,v in original['reading_anchors'].items() if k in mapping}
    if after.get('analysis',{}).get('reading_anchors',{})!=anchors:errors.append('Protected reading anchors changed')
    ocr=copy.deepcopy(original['text_check'])
    if ocr:ocr['regions']=[dict(r,region_id=mapping[r['region_id']]) for r in ocr['regions'] if r['region_id'] in mapping]
    if after.get('analysis',{}).get('text_check')!=ocr:errors.append('Protected spatial OCR changed')
    if after['review'].get('verified') is not False:errors.append('Filtered page falsely marked verified')
    return errors


def compare_text_additions(before, after, rule):
    """Fixed visual approvals plus independent native OCR; keep every old stop.

    The policy is written after inspecting originals. Candidate recovery audits
    cannot authorize additions, changed contours or a reordered old dialogue.
    """
    errors=[];a,b=before['result'],after['result']
    old={r['id']:r for r in a['bubbles']};new={r['id']:r for r in b['bubbles']}
    mapping=rule['preserved_regions'];additions=rule['additions']
    targets=[v['region']['id'] for v in additions]
    if (not additions or set(mapping)!=set(old) or len(set(mapping.values()))!=len(mapping)
            or len(set(targets))!=len(targets) or set(targets)&set(mapping.values())
            or set(targets)|set(mapping.values())!=set(new)):
        return ['Incomplete or duplicated addition mapping']
    if {k:v for k,v in a.items() if k not in {'bubbles','confidence'}}!={k:v for k,v in b.items() if k not in {'bubbles','confidence'}}:
        errors.append('Page metadata or panels changed during addition')
    if any(r['id']!=f'b{i+1}' or r['order']!=i+1 for i,r in enumerate(b['bubbles'])):
        errors.append('Invalid addition reading-order metadata')
    if not math.isclose(b['confidence'],sum(r['confidence'] for r in b['bubbles'])/max(1,len(b['bubbles'])),abs_tol=1e-12):
        errors.append('Invalid aggregate addition confidence')
    if [new[mapping[r['id']]]['order'] for r in a['bubbles']]!=sorted(new[mapping[r['id']]]['order'] for r in a['bubbles']):
        errors.append('Existing dialogue reordered during addition')
    for old_id,new_id in mapping.items():
        if {k:v for k,v in old[old_id].items() if k not in {'id','order'}}!={k:v for k,v in new[new_id].items() if k not in {'id','order'}}:
            errors.append('Protected region changed during addition: '+old_id)
        if before.get('analysis',{}).get('reading_anchors',{}).get(old_id)!=after.get('analysis',{}).get('reading_anchors',{}).get(new_id):
            errors.append('Protected reading anchor changed during addition: '+old_id)
    previous_ocr=before.get('analysis',{}).get('text_check',{}).get('regions',[])
    current_ocr=after.get('analysis',{}).get('text_check',{}).get('regions',[])
    for row in previous_ocr:
        expected=dict(row,region_id=mapping[row['region_id']])
        if expected not in current_ocr:errors.append('Protected spatial OCR changed during addition: '+row['region_id'])
    width,height=a['width'],a['height']
    for addition in additions:
        target=addition['region'];rows=addition.get('native_ocr',[])
        if new[target['id']]!=target:errors.append('Unreviewed added geometry or order: '+target['id'])
        if (target.get('type')!='text' or target.get('polygons') or target.get('polygon')
                or any(not math.isfinite(target[k]) for k in ('x','y','w','h'))
                or min(target['w'],target['h'])<=0 or min(target['x'],target['y'])<0
                or target['x']+target['w']>1.000001 or target['y']+target['h']>1.000001):
            errors.append('Invalid added text rectangle')
        if addition.get('image_sha256')!=before.get('lab',{}).get('sha256') or not rows:
            errors.append('Missing independent native OCR evidence');continue
        bounds=[target['x']*width,target['y']*height,(target['x']+target['w'])*width,(target['y']+target['h'])*height]
        for row in rows:
            box=row.get('box',[])
            if (row.get('score',0)<.85 or not row.get('text') or len(box)!=4
                    or any(not math.isfinite(v) for v in box)
                    or not (bounds[0]<=box[0]+.1<box[2]<=bounds[2]+.1 and bounds[1]<=box[1]+.1<box[3]<=bounds[3]+.1)):
                errors.append('Added region cuts or lacks a confirmed native OCR line')
    if after['review'].get('verified') is not False:errors.append('Recovered page falsely marked verified')
    return errors


def compare(baseline, candidate, policy):
    old={p.name:p for p in baseline.glob('*.json') if p.name!='results.json'}
    new={p.name:p for p in candidate.glob('*.json') if p.name!='results.json'}
    errors=[];changes=[];order_changes=[];split_changes=[];removals=[];additions=[];contexts=[];unchanged=0;regions=0;seen_order_rules=set();seen_split_rules=set();seen_removals=set();seen_additions=set();seen_contexts=set()
    if not old:
        errors.append('Empty baseline')
    if old.keys()!=new.keys():
        errors.append('Different page sets')
    for name in sorted(old.keys() & new.keys()):
        a=json.loads(old[name].read_text(encoding='utf-8'))
        b=json.loads(new[name].read_text(encoding='utf-8'))
        identity=a.get('lab',{}).get('sha256')
        if not identity or identity!=b.get('lab',{}).get('sha256'):
            errors.append(name+': different image identity')
            continue
        ra,rb=a['result'],b['result']
        context_rule=next((r for r in policy.get('context_changes',[]) if r['sha_prefix'] in name),None)
        if context_rule:
            seen_contexts.add(context_rule['sha_prefix']);regions+=len(ra['bubbles'])
            errors.extend(name+': '+e for e in compare_context_change(a,b,context_rule))
            contexts.append(dict(page=name,reason=context_rule['reason']))
            continue
        addition_rule=next((r for r in policy.get('text_additions',[]) if r['sha_prefix'] in name),None)
        if addition_rule:
            seen_additions.add(addition_rule['sha_prefix']);regions+=len(ra['bubbles'])
            errors.extend(name+': '+e for e in compare_text_additions(a,b,addition_rule))
            additions.append({'page':name,'added_regions':[r['region']['id'] for r in addition_rule['additions']],
                              'reason':addition_rule['reason']})
            continue
        removal_rule=next((r for r in policy.get('content_removals',[]) if r['sha_prefix'] in name),None)
        if removal_rule:
            seen_removals.add(removal_rule['sha_prefix']);regions+=len(ra['bubbles'])
            errors.extend(name+': '+e for e in compare_content_removals(a,b,removal_rule))
            removals.append({'page':name,'removed_region_ids':removal_rule['removed_region_ids'],
                             'reason':removal_rule['reason']})
            continue
        split_rule=next((r for r in policy.get('text_split_changes',[]) if r['sha_prefix'] in name),None)
        if split_rule:
            seen_split_rules.add(split_rule['sha_prefix']);regions+=len(ra['bubbles'])
            errors.extend(name+': '+e for e in compare_text_splits(a,b,split_rule))
            split_changes.append({'page':name,'splits':len(split_rule['splits']),'reason':split_rule['reason']})
            continue
        old_ids={r['id']:r['id'] for r in ra['bubbles']}
        order_rule=next((r for r in policy.get('reading_order_changes',[]) if r['sha_prefix'] in name),None)
        if order_rule:
            seen_order_rules.add(order_rule['sha_prefix'])
            sequence=order_rule['old_region_sequence']
            panel_sequence=order_rule.get('old_panel_sequence',[p['id'] for p in ra['panels']])
            if (len(sequence)!=len(set(sequence)) or set(sequence)!={r['id'] for r in ra['bubbles']}
                    or len(panel_sequence)!=len(set(panel_sequence)) or set(panel_sequence)!={p['id'] for p in ra['panels']}):
                errors.append(name+': invalid reviewed reading-order permutation');continue
            if ra==rb:errors.append(name+': required reading-order correction absent')
            original=ra;ra=copy.deepcopy(ra)
            panels={p['id']:p for p in ra['panels']};mapping={old:f'p{i+1}' for i,old in enumerate(panel_sequence)}
            ra['panels']=[dict(panels[old],id=mapping[old],order=i+1) for i,old in enumerate(panel_sequence)]
            boxes={r['id']:r for r in ra['bubbles']}
            ra['bubbles']=[dict(boxes[old],id=f'b{i+1}',order=i+1,
                                panel_id=mapping.get(boxes[old].get('panel_id'))) for i,old in enumerate(sequence)]
            old_ids={f'b{i+1}':old for i,old in enumerate(sequence)}
            order_changes.append({'page':name,'old_region_sequence':sequence,'old_panel_sequence':panel_sequence,
                                  'reason':order_rule['reason']})
        rules={r['region_id']:r for r in policy.get('changes',[]) if r['sha_prefix'] in name}
        if set(rules)-set(old_ids.values()):
            errors.append(name+': policy names a nonexistent baseline region')
        if {k:v for k,v in ra.items() if k!='bubbles'}!={k:v for k,v in rb.items() if k!='bubbles'}:
            errors.append(name+': page/panel/order metadata changed')
        if [r['id'] for r in ra['bubbles']]!=[r['id'] for r in rb['bubbles']]:
            errors.append(name+': missing, extra or reordered regions')
            continue
        page_changed=bool(order_rule)
        for before,after in zip(ra['bubbles'],rb['bubbles']):
            regions+=1;original_id=old_ids[before['id']];rule=rules.get(original_id)
            if not rule:
                if before!=after:errors.append(name+': protected region changed: '+before['id'])
                continue
            page_changed=True
            allowed=set(rule['allowed_fields'])
            if before==after:errors.append(name+': required correction absent: '+before['id'])
            if {k:v for k,v in before.items() if k not in allowed}!={k:v for k,v in after.items() if k not in allowed}:
                errors.append(name+': protected identity/order/confidence changed: '+before['id'])
            if rule.get('shape')=='contour_extension':
                if after.get('type')!=rule['expected_type']:
                    errors.append(name+': contour classification changed')
                issue=contour_extension(before,after,ra['width'],ra['height'],rule)
                if issue:errors.append(name+': '+issue+': '+before['id'])
            elif after.get('type')!=rule['expected_type'] or after.get('polygons') or after.get('polygon'):
                errors.append(name+': expected text rectangle missing: '+before['id'])
            ratio=after['w']*after['h']/max(1e-12,before['w']*before['h'])
            if ratio>rule['max_bbox_area_ratio']:errors.append(name+': artwork area not sufficiently reduced')
            # Existing OCR positions are an independent no-clipped-words gate.
            check=next((r for r in a.get('analysis',{}).get('text_check',{}).get('regions',[]) if r['region_id']==original_id),None)
            if not check or not check.get('ocr'):
                errors.append(name+': missing spatial OCR evidence for correction')
            else:
                width,height=ra['width'],ra['height']
                x1,y1,x2,y2=check['box']
                for row in check['ocr']:
                    if not row.get('box'):
                        errors.append(name+': OCR has no spatial evidence');continue
                    u,v,w,z=row['box']
                    px1,py1=x1+u*(x2-x1),y1+v*(y2-y1)
                    px2,py2=x1+w*(x2-x1),y1+z*(y2-y1)
                    if not (after['x']*width<=px1 and after['y']*height<=py1
                            and (after['x']+after['w'])*width>=px2 and (after['y']+after['h'])*height>=py2):
                        errors.append(name+': clipped OCR line: '+row['text'])
            changes.append({'page':name,'region':original_id,'bbox_area_ratio':round(ratio,5),'reason':rule.get('reason','Reviewed geometry correction')})
        unchanged+=not page_changed
    missing_order_rules={r['sha_prefix'] for r in policy.get('reading_order_changes',[])}-seen_order_rules
    if missing_order_rules:errors.append('Missing reviewed reading-order pages: '+','.join(sorted(missing_order_rules)))
    missing_split_rules={r['sha_prefix'] for r in policy.get('text_split_changes',[])}-seen_split_rules
    if missing_split_rules:errors.append('Missing reviewed text-split pages: '+','.join(sorted(missing_split_rules)))
    missing_removals={r['sha_prefix'] for r in policy.get('content_removals',[])}-seen_removals
    if missing_removals:errors.append('Missing reviewed content-removal pages: '+','.join(sorted(missing_removals)))
    missing_additions={r['sha_prefix'] for r in policy.get('text_additions',[])}-seen_additions
    if missing_additions:errors.append('Missing reviewed text-addition pages: '+','.join(sorted(missing_additions)))
    missing_contexts={r['sha_prefix'] for r in policy.get('context_changes',[])}-seen_contexts
    if missing_contexts:errors.append('Missing reviewed context pages: '+','.join(sorted(missing_contexts)))
    return {'passed':not errors,'pages':len(old),'regions':regions,'unchanged_pages':unchanged,'approved_changes':changes,
            'approved_order_changes':order_changes,'approved_text_splits':split_changes,'approved_content_removals':removals,'approved_text_additions':additions,'approved_context_changes':contexts,'errors':errors,
            'scope':'Exact comparison to baseline, not a general accuracy measurement.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Blokada regresji względem zamrożonych wyników')
    for name in ('baseline','candidate','policy','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    result=compare(args.baseline,args.candidate,json.loads(args.policy.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
