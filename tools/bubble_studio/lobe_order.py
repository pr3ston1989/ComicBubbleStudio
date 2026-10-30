"""Order a connected balloon by its leading physical lobe, not its whole span."""
import copy
import re
import cv2
import numpy as np
from .compound_guard import _texts
from .quality_guard import _polygons
from .textcheck import pixel_box
from .strip_reader import _body_anchor
from .body_order import _overlap
from web.backend.comic_smartview_layout import order_boxes_in_rows


def leading_lobe(image, document, bubble, panel):
    texts = _texts(image, document, bubble)
    if not texts or not all(t.get('label') == 1 and t.get('score', 0) >= .7 for t in texts):
        return None
    if len(bubble.get('polygons', [])) != 1:
        return None
    roi = pixel_box(bubble, image.size)
    if (roi[2]-roi[0]) * (roi[3]-roi[1]) > 4_000_000:
        return None
    mask = np.zeros((roi[3]-roi[1], roi[2]-roi[0]), np.uint8)
    cv2.fillPoly(mask, _polygons(bubble, *image.size, roi[:2]), 1)
    size = max(5, round(min(mask.shape) * .12)) | 1
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    _, labels, stats, _ = cv2.connectedComponentsWithStats(opened, 8)
    check=next((r for r in document['analysis'].get('text_check',{}).get('regions',[]) if r['region_id']==bubble['id']),None)
    if not check:return None
    ox,oy,right,bottom=check['box'];groups={}
    for row in check.get('ocr',[]):
        if row.get('score',0)<.9 or not row.get('text','').strip():continue
        a,b,c,d=row['box'];a,c=ox+a*(right-ox),ox+c*(right-ox);b,d=oy+b*(bottom-oy),oy+d*(bottom-oy)
        cx,cy = round((a+c)/2-roi[0]),round((b+d)/2-roi[1])
        if not 0 <= cy < mask.shape[0] or not 0 <= cx < mask.shape[1]:continue
        # Independent OCR reads the rectangular crop, including words in
        # neighbouring balloons inside a compound's empty bounding-box space.
        # Such words must never become evidence for this balloon's lobes.
        if not mask[cy,cx]:continue
        index = labels[cy,cx]
        if index == 0:continue
        x,y,w,h,area = stats[index]
        if area < np.sum(mask) * .07:return None
        groups.setdefault(index,[]).append((a,b,c,d))
    components={};gray=cv2.cvtColor(np.asarray(image.crop(roi)),cv2.COLOR_RGB2GRAY)
    for index,rows in groups.items():
        x,y,w,h,area=stats[index];a=min(r[0] for r in rows);b=min(r[1] for r in rows);c=max(r[2] for r in rows);d=max(r[3] for r in rows)
        if w*h>(c-a)*(d-b)*7:return None
        pixels=gray[labels==index];median=float(np.median(pixels))
        if not (median>195 or median<60) or np.mean(np.abs(pixels.astype(float)-median)<=24)<.65:return None
        components[index]=dict(x=(roi[0]+x)/image.width,y=max(panel['y'],(roi[1]+y)/image.height),w=w/image.width,h=h/image.height)
    if len(components) < 2:return None
    return order_boxes_in_rows(list(components.values()),document['result']['direction'],align_starts=False)[0]


def refine_lobe_order(image, document):
    if document.get('review', {}).get('verified'):return document
    original=copy.deepcopy(document);result=document['result'];bubbles=result['bubbles'];anchors=document['analysis'].get('reading_anchors',{})
    if set(anchors)!={b['id'] for b in bubbles}:return document
    identities={id(b):b['id'] for b in bubbles}
    panels=list(result['panels'])
    orphan_bands=[]
    for bubble in sorted((b for b in bubbles if b.get('panel_id') is None),key=lambda b:b['y']):
        if not orphan_bands or bubble['y']>max(b['y']+b['h'] for b in orphan_bands[-1]):orphan_bands.append([])
        orphan_bands[-1].append(bubble)
    for band in orphan_bands:
        if len(band)>1 and max(b['y']+b['h'] for b in band)-min(b['y'] for b in band)<=.35:
            panels.append(dict(id=None,y=0,h=1,_orphan_ids={b['id'] for b in band}))
    for panel in panels:
        indices=[i for i,b in enumerate(bubbles) if b.get('panel_id')==panel['id'] and ('_orphan_ids' not in panel or b['id'] in panel['_orphan_ids'])]
        group=[bubbles[i] for i in indices]
        if len(group)<2 or any(b.get('type')!='bubble' or not b.get('polygons') for b in group):continue
        lobes=[leading_lobe(image,document,b,panel) for b in group]
        if not any(p is not None for p in lobes):continue
        proxies=[lobe if lobe is not None else _body_anchor(image,b,anchors[b['id']],panel) for b,lobe in zip(group,lobes)]
        if any(lobe is None and p['y']==anchors[b['id']]['y'] and p['h']==anchors[b['id']]['h'] for b,p,lobe in zip(group,proxies,lobes)):continue
        if any(_overlap(a,b)>.8 for i,a in enumerate(proxies) for b in proxies[i+1:]):continue
        lookup={id(p):b for p,b in zip(proxies,group)}
        ordered=[lookup[id(p)] for p in order_boxes_in_rows(proxies,result['direction'],align_starts=False)]
        for i,b in zip(indices,ordered):bubbles[i]=b
    mapping={identities[id(b)]:f'b{i+1}' for i,b in enumerate(bubbles)}
    if all(k==v for k,v in mapping.items()):return document
    for i,b in enumerate(bubbles):b.update(id=f'b{i+1}',order=i+1)
    document['analysis']['reading_anchors']={mapping[k]:v for k,v in anchors.items()}
    for row in document['analysis'].get('text_check',{}).get('regions',[]):row['region_id']=mapping[row['region_id']]
    document['review']['flags']=[re.sub(r'\bb\d+\b',lambda m:mapping.get(m[0],m[0]),s) for s in document['review']['flags']]
    audit=dict(kind='leading-native-lobe-order',mapping=mapping);document['analysis']['leading_lobe_order']=audit
    context=document['analysis'].setdefault('page_context',{});context.setdefault('original',original);context['status']='applied';context.setdefault('changes',[]).append(audit)
    document['review']['flags'].append('Kolejność połączonego dymka ustalono od jego pierwszego członu; sprawdź podgląd')
    return document
