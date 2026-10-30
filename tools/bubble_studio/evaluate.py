"""Compare packages with hand-reviewed reference contours at native resolution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from web.backend.comic_bubble_package import read_manifest


def rasterize(box, width, height):
    mask = np.zeros((height, width), np.uint8)
    polygons = box.get('polygons') or ([box['polygon']] if box.get('polygon') else [])
    if polygons:
        for polygon in polygons:
            points = np.array([[(box['x']+p['x']*box['w'])*width,
                                (box['y']+p['y']*box['h'])*height] for p in polygon])
            cv2.fillPoly(mask, [np.rint(points).astype(np.int32)], 1)
    else:
        x1,y1,x2,y2 = np.rint([box['x']*width,box['y']*height,
                             (box['x']+box['w'])*width,(box['y']+box['h'])*height]).astype(int)
        mask[max(0,y1):min(height,y2),max(0,x1):min(width,x2)] = 1
    return mask


def boundary_fscore(reference, prediction, tolerance=3):
    kernel = np.ones((3,3),np.uint8)
    a = reference-cv2.erode(reference,kernel,borderType=cv2.BORDER_CONSTANT,borderValue=0)
    b = prediction-cv2.erode(prediction,kernel,borderType=cv2.BORDER_CONSTANT,borderValue=0)
    radius=np.ones((2*tolerance+1,2*tolerance+1),np.uint8)
    precision=np.count_nonzero((b>0)&(cv2.dilate(a,radius)>0))/max(1,np.count_nonzero(b))
    recall=np.count_nonzero((a>0)&(cv2.dilate(b,radius)>0))/max(1,np.count_nonzero(a))
    return 2*precision*recall/max(1e-12,precision+recall)


def compare_page(reference, prediction, tolerance=3):
    width,height = reference['width'],reference['height']
    if (width,height) != (prediction['width'],prediction['height']):
        raise ValueError('Różne rozmiary tej samej strony')
    if width*height > 25_000_000:
        raise ValueError('Strona zbyt duża do oceny; podziel długi pasek')
    refs,preds = reference['bubbles'],prediction['bubbles']
    # Keep only one pair of full-resolution masks in memory at a time.
    matrix=np.zeros((len(refs),len(preds)),np.float64)
    for i,ref in enumerate(refs):
        a=rasterize(ref,width,height)
        for j,pred in enumerate(preds):
            b=rasterize(pred,width,height)
            matrix[i,j]=np.count_nonzero((a>0)&(b>0))/max(1,np.count_nonzero((a>0)|(b>0)))
    # Prefer the number of valid matches before their summed IoU. Otherwise a
    # very good pair plus a subthreshold pair could displace two valid pairs.
    objective=(matrix >= .5).astype(float) + matrix/max(1,min(matrix.shape))
    rows,cols=linear_sum_assignment(objective,maximize=True)
    pairs=[]
    for i,j in zip(rows,cols):
        if matrix[i,j] >= .5:
            a,b=rasterize(refs[i],width,height),rasterize(preds[j],width,height)
            pairs.append({'reference':int(i),'prediction':int(j),'iou':round(float(matrix[i,j]),5),
                          'boundary_f':round(boundary_fscore(a,b,tolerance),5)})
    count=len(pairs)
    # Only compare order where geometry establishes a 1:1 match. Missing regions
    # remain in recall, never silently counted as correct reading order.
    matched = sorted(pairs, key=lambda pair: pair['reference'])
    comparable = count*(count-1)//2
    inversions = sum(a['prediction'] > b['prediction']
                     for i,a in enumerate(matched) for b in matched[i+1:])
    return {'reference_regions':len(refs),'predicted_regions':len(preds), 'matched_at_iou_50':count,
            'missed':len(refs)-count,'extra':len(preds)-count,'pairs':pairs,
            'order_pairs': comparable, 'order_inversions': inversions,
            'matched_order_agreement': (comparable-inversions)/comparable if comparable else None,
            'direction_matches': reference.get('direction') == prediction.get('direction'),
            'reference_text_regions': sum(b.get('type')=='text' for b in refs),
            'matched_text_regions': sum(refs[p['reference']].get('type')=='text' for p in pairs),
            'rectangles':sum(not b.get('polygons') and not b.get('polygon') for b in preds)}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Ocena względem ręcznie sprawdzonych obrysów')
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--prediction',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tolerance',type=int,default=3)
    args=parser.parse_args(argv)
    if not 1 <= args.tolerance <= 20:
        parser.error('Tolerancja musi wynosić 1–20 pikseli')
    ref,pred=read_manifest(args.reference),read_manifest(args.prediction)
    if ref['source']['sha256'] != pred['source']['sha256'] or len(ref['pages']) != len(pred['pages']):
        raise ValueError('Pakiety dotyczą różnych komiksów')
    if [p['sha256'] for p in ref['pages']] != [p['sha256'] for p in pred['pages']]:
        raise ValueError('Pakiety zawierają różne strony')
    pages=[]
    with zipfile.ZipFile(args.reference) as a,zipfile.ZipFile(args.prediction) as b:
        for page in ref['pages']:
            r,p=json.loads(a.read(page['data'])),json.loads(b.read(page['data']))
            if r.get('review',{}).get('verified') is not True:
                continue
            metrics=compare_page(r['result'],p['result'],args.tolerance)
            pages.append({'page':page['index']+1,**metrics})
    if not pages:
        raise ValueError('Brak ręcznie zatwierdzonych stron referencyjnych')
    pairs=[pair for page in pages for pair in page['pairs']]
    total_ref=sum(p['reference_regions'] for p in pages)
    total_pred=sum(p['predicted_regions'] for p in pages)
    order_pairs=sum(p['order_pairs'] for p in pages)
    inversions=sum(p['order_inversions'] for p in pages)
    result={'evaluated_pages':len(pages),'reference_regions':total_ref,'predicted_regions':total_pred,
            'recall_at_iou_50':len(pairs)/max(1,total_ref),'precision_at_iou_50':len(pairs)/max(1,total_pred),
            'mean_matched_iou':float(np.mean([p['iou'] for p in pairs])) if pairs else None,
            'mean_matched_boundary_f':float(np.mean([p['boundary_f'] for p in pairs])) if pairs else None,
            'matched_order_agreement': (order_pairs-inversions)/order_pairs if order_pairs else None,
            'order_pairs': order_pairs, 'order_inversions': inversions,
            'direction_mismatches': sum(not p['direction_matches'] for p in pages),
            'boundary_tolerance_px':args.tolerance,'pages':pages,
            'note':'Tylko strony zatwierdzone ręcznie; średnie IoU i boundary F dotyczą dopasowanych regionów.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
