"""Complete-page reading-stop assessment, separate from mask-boundary accuracy."""
import argparse
import json
import hashlib
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment


def contains(region,point):
    x,y=point
    polygons=region.get('polygons') or ([region['polygon']] if region.get('polygon') else [])
    if not polygons:
        return region['x']<=x<=region['x']+region['w'] and region['y']<=y<=region['y']+region['h']
    contours=[np.array([[(region['x']+p['x']*region['w']),(region['y']+p['y']*region['h'])]
                        for p in poly],np.float32) for poly in polygons]
    return any(cv2.pointPolygonTest(c,(float(x),float(y)),False)>=0 for c in contours)


def score_page(reference,document):
    if not reference.get('complete'):
        raise ValueError('Only complete-page reading lists may be scored')
    if not reference.get('image_sha256') or document.get('lab',{}).get('sha256')!=reference['image_sha256']:
        raise ValueError('Reference and prediction have different image identities')
    refs=reference['utterances'];preds=document['result']['bubbles']
    eligible=np.zeros((len(refs),len(preds)),bool)
    costs=np.full(eligible.shape,1000.0)
    for i,ref in enumerate(refs):
        if not ref.get('points'):raise ValueError('Utterance has no spatial reference')
        for j,pred in enumerate(preds):
            eligible[i,j]=all(contains(pred,p) for p in ref['points'])
            # Assignment uses geometry only. Reading order cannot influence
            # matching, otherwise its own evaluation could conceal inversions.
            if eligible[i,j]:costs[i,j]=pred['w']*pred['h']*.001
    pairs=[]
    if len(refs) and len(preds):
        rows,cols=linear_sum_assignment(costs)
        pairs=[(int(i),int(j)) for i,j in zip(rows,cols) if eligible[i,j]]
    pairs.sort()
    mapped=dict(pairs);matched={j for i,j in pairs}
    orders=[preds[j]['order'] for i,j in pairs]
    inversions=sum(a>b for i,a in enumerate(orders) for b in orders[i+1:])
    excluded=[]
    for i,j in pairs:
        for point in refs[i].get('exclude_points',[]):
            if contains(preds[j],point):excluded.append({'utterance':i+1,'predicted_region':preds[j]['id'],'point':point})
    missing=[{'utterance':i+1,'label':r['label']} for i,r in enumerate(refs) if i not in mapped]
    extras=[preds[j]['id'] for j in range(len(preds)) if j not in matched]
    direction_matches=reference['direction']==document['result']['direction']
    invalid_metadata=any(p['order']!=i+1 for i,p in enumerate(preds))
    complete=not missing and not extras and not inversions and direction_matches and not invalid_metadata
    return {'sha_prefix':reference['sha_prefix'],'name':reference['name'],'split':reference.get('split'),
            'direction':reference['direction'],'reference_stops':len(refs),'predicted_stops':len(preds),
            'matched_stops':len(pairs),'missing':missing,'extra_regions':extras,'order_inversions':inversions,
            'order_pairs':len(pairs)*(len(pairs)-1)//2,'direction_matches':direction_matches,
            'invalid_order_metadata':invalid_metadata,'complete_reading_success':complete,
            'outline_exclusion_failures':excluded,
            'sequence':[{'utterance':i+1,'label':ref['label'],'predicted_region':preds[mapped[i]]['id'] if i in mapped else None,
                         'predicted_order':preds[mapped[i]]['order'] if i in mapped else None} for i,ref in enumerate(refs)]}


def evaluate(reference,folder):
    pages=[]
    for ref in reference['pages']:
        paths=list(folder.glob('*'+ref['sha_prefix']+'.json'))
        if len(paths)!=1:raise ValueError('Missing or ambiguous page: '+ref['sha_prefix'])
        pages.append(score_page(ref,json.loads(paths[0].read_text(encoding='utf-8'))))
    def summary(group):
        refs=sum(p['reference_stops'] for p in group);preds=sum(p['predicted_stops'] for p in group)
        matched=sum(p['matched_stops'] for p in group);pairs=sum(p['order_pairs'] for p in group);inv=sum(p['order_inversions'] for p in group)
        return {'pages':len(group),'reference_stops':refs,'predicted_stops':preds,'matched_stops':matched,
                'missing_stops':refs-matched,'extra_stops':preds-matched,'stop_recall':matched/refs if refs else None,
                'stop_precision':matched/preds if preds else None,'order_pairs':pairs,'order_inversions':inv,
                'matched_order_agreement':(pairs-inv)/pairs if pairs else None,
                'complete_reading_pages':sum(p['complete_reading_success'] for p in group),
                'outline_exclusion_failures':sum(len(p['outline_exclusion_failures']) for p in group)}
    signature=hashlib.sha256(json.dumps(reference,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    return {'reference_sha256':signature,'scope':reference['scope'],'policy':reference['policy'],'overall':summary(pages),
            'by_direction':{direction:summary([p for p in pages if p['direction']==direction]) for direction in ('ltr','rtl')},
            'pages':pages,'note':'Full lists on these selected pages only. Stop matching does not measure complete contour fidelity. Inspect the reference and all failures.'}


def compare_evaluations(before,after):
    errors=[];improved=[]
    if not before.get('reference_sha256') or before['reference_sha256']!=after.get('reference_sha256'):
        errors.append('Different reference definitions')
    a={p['sha_prefix']:p for p in before['pages']};b={p['sha_prefix']:p for p in after['pages']}
    if a.keys()!=b.keys():errors.append('Different reference page sets')
    for key in sorted(a.keys()&b.keys()):
        old,new=a[key],b[key]
        old_counts=[len(old['missing']),len(old['extra_regions']),old['order_inversions'],len(old['outline_exclusion_failures'])]
        new_counts=[len(new['missing']),len(new['extra_regions']),new['order_inversions'],len(new['outline_exclusion_failures'])]
        if old['reference_stops']!=new['reference_stops']:errors.append(key+': different expected reading stops')
        if any(x>y for x,y in zip(new_counts,old_counts)):errors.append(key+': worse missing/extra/order/outline observations')
        if not new['direction_matches'] or new['invalid_order_metadata']:errors.append(key+': invalid direction or order metadata')
        if any(x<y for x,y in zip(new_counts,old_counts)):improved.append(key)
    return {'passed':not errors,'pages':len(a),'improved_pages':improved,'errors':errors,
            'scope':'No worsening on the same complete-page reading reference; existing errors remain visible.'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Ocena pełnych list wypowiedzi na opisanych stronach')
    parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv);result=evaluate(json.loads(args.reference.read_text(encoding='utf-8')),args.results)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['pages','policy','scope']},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
