"""Merge only physically connected native enclosures, preserving every old pixel."""
import copy
import re
import cv2
import numpy as np
from .geometry import rectangle,contour_box
from .quality_guard import _polygons,overlap_share
from .textcheck import pixel_box
from .segmentation import ink_evidence
from .native_enclosures import enclosure_candidates
from .thin_bridges import bridge_candidates


def _texts(image,document,member):
    anchor=document['analysis'].get('reading_anchors',{}).get(member['id'])
    if not anchor:return []
    matches=[]
    for diagnostic in document['analysis'].get('balloons',[]):
        rows=diagnostic.get('supporting_texts',[])
        if not rows:continue
        box=[min(t['box'][0] for t in rows),min(t['box'][1] for t in rows),max(t['box'][2] for t in rows),max(t['box'][3] for t in rows)]
        normalized=rectangle(box,*image.size,1,margin=0)
        if all(abs(normalized[k]-anchor[k])<1e-6 for k in ('x','y','w','h')):matches.append(rows)
    return matches[0] if len(matches)==1 else []


def _raster(region,size):
    mask=np.zeros((size[1],size[0]),np.uint8)
    if region.get('polygons'):cv2.fillPoly(mask,_polygons(region,*size,(0,0)),1)
    else:
        x,y,xx,yy=pixel_box(region,size);mask[y:yy,x:xx]=1
    return mask


def _conflicts(candidate,members,document,size):
    ids={b['id'] for b in members};others=[b for b in document['result']['bubbles'] if b['id'] not in ids]
    if any(overlap_share(candidate,b,*size)>.03 for b in others if b.get('polygons')):return True
    roi=pixel_box(candidate,size);mask=np.zeros((roi[3]-roi[1],roi[2]-roi[0]),np.uint8)
    cv2.fillPoly(mask,_polygons(candidate,*size,roi[:2]),1)
    for b in others:
        anchor=document['analysis']['reading_anchors'].get(b['id'],b);box=pixel_box(anchor,size)
        x1,y1=max(0,box[0]-roi[0]),max(0,box[1]-roi[1]);x2,y2=min(mask.shape[1],box[2]-roi[0]),min(mask.shape[0],box[3]-roi[1])
        if x2>x1 and y2>y1 and np.any(mask[y1:y2,x1:x2]):return True
    return False


def _text_preserved(image,document,region,mask):
    rows=_texts(image,document,region)
    evidence,reliable=ink_evidence(image,rows,(0,0))
    if reliable!=len(rows) or not reliable:return False
    if np.count_nonzero((evidence>0)&(mask>0))/max(1,np.count_nonzero(evidence))<.995:return False
    check=next((r for r in document['analysis'].get('text_check',{}).get('regions',[]) if r['region_id']==region['id']),None)
    if check:
        x,y,xx,yy=check['box']
        for row in check.get('ocr',[]):
            if row.get('score',0)<.75 or not row.get('text','').strip():continue
            box=row.get('box')
            if not box or len(box)!=4:return False
            a,b,c,d=x+box[0]*(xx-x),y+box[1]*(yy-y),x+box[2]*(xx-x),y+box[3]*(yy-y)
            dx,dy=(c-a)*.08,(d-b)*.08;a,b=max(0,int(a+dx)),max(0,int(b+dy));c,d=min(image.width,int(np.ceil(c-dx))),min(image.height,int(np.ceil(d-dy)))
            if c<=a or d<=b or np.mean(mask[b:d,a:c])<.98:return False
    return True


def recover_compounds(image,document,checker):
    if document.get('review',{}).get('verified'):return document
    original=copy.deepcopy(document);bubbles=document['result']['bubbles']
    proposals=[(*p,'enclosure') for p in enclosure_candidates(image,document)]
    proposals += [(*p,'bridge') for p in bridge_candidates(image,document)]
    selected=[];used=set()
    for ids,proposal,audit,kind in proposals:
        if used.intersection(ids):continue
        members=[b for b in bubbles if b['id'] in ids]
        if len(members)!=len(ids):continue
        texts=[t for b in members for t in _texts(image,document,b)]
        if not texts or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in texts):continue
        extra={}
        # Open white background around text rectangles cannot establish that
        # two speakers share a balloon. Require an existing physical outline
        # at both ends of a visible thin connector.
        if kind=='bridge' and (any(not b.get('polygons') for b in members) or not audit.get('bridge_pixels')):
            continue
        # A text fallback rectangle has no physical contour. Retaining its
        # empty corners would create rectangular spikes on a recovered ellipse.
        # Preserve actual letter ink and independent OCR boxes instead.
        old_masks=[_raster(b,image.size) for b in members if b.get('polygons')];mask=_raster(proposal,image.size)
        if not old_masks:continue
        if any(not _text_preserved(image,document,b,mask) for b in members if not b.get('polygons')):continue
        for old in old_masks:mask|=old
        region=contour_box(mask,(0,0),*image.size,min(b['confidence'] for b in members),epsilon=.1,max_vertices=2048)
        if len(region['polygons'])!=1 or _conflicts(region,members,document,image.size):continue
        exported=_raster(region,image.size);preserved=[float(np.sum(exported&old)/max(1,np.sum(old))) for old in old_masks]
        if min(preserved)<.999:continue
        if any(not _text_preserved(image,document,b,exported) for b in members if not b.get('polygons')):continue
        first=min(members,key=lambda b:b['order']);region.update(id=first['id'],order=first['order'],panel_id=first.get('panel_id'))
        bounds=[min(t['box'][0] for t in texts),min(t['box'][1] for t in texts),max(t['box'][2] for t in texts),max(t['box'][3] for t in texts)]
        anchor=rectangle(bounds,*image.size,1,margin=0)
        record=dict(ids=list(ids),first=first['id'],region=region,anchor={k:anchor[k] for k in ('x','y','w','h')},
            supporting_texts=texts,original_regions=copy.deepcopy(members),mask_preserved=preserved,
            text_rectangles_checked='native-letter-ink+independent-OCR-boxes',**audit,**(extra or {}))
        selected.append(record);used.update(ids)
    if not selected:return document
    replacements={r['first']:r for r in selected};removed={i for r in selected for i in r['ids'] if i!=r['first']}
    proposed=[replacements[b['id']]['region'] if b['id'] in replacements else b for b in bubbles if b['id'] not in removed]
    if sum(len(p) for b in proposed for p in b.get('polygons',[]))>32000:return document
    saved=document['analysis']['reading_anchors'];anchors={}
    for b in proposed:
        anchors[b['id']]=replacements[b['id']]['anchor'] if b['id'] in replacements else saved[b['id']]
    mapping={b['id']:f'b{i+1}' for i,b in enumerate(proposed)}
    for record in selected:
        document['analysis'].setdefault('balloons',[]).append(dict(method='native-connected-compound',
            supporting_texts=record['supporting_texts'],detection_box=list(pixel_box(record['region'],image.size))))
    for i,b in enumerate(proposed):b.update(id=f'b{i+1}',order=i+1)
    document['result']['bubbles']=proposed
    document['result']['confidence']=sum(b['confidence'] for b in proposed)/max(1,len(proposed))
    document['analysis']['reading_anchors']={mapping[k]:v for k,v in anchors.items()}
    old_to_first={i:r['first'] for r in selected for i in r['ids']}
    full_mapping={b['id']:mapping[old_to_first.get(b['id'],b['id'])] for b in original['result']['bubbles']}
    document['review']['flags']=[re.sub(r'\bb\d+\b',lambda m:full_mapping.get(m[0],m[0]),s) for s in document['review']['flags']]
    checker.review(image,document)
    audit=dict(kind='native-connected-compounds',groups=selected,mapping=full_mapping)
    document['analysis']['native_compounds']=audit
    context=document['analysis'].setdefault('page_context',{})
    context.setdefault('original',original);context['status']='applied';context.setdefault('changes',[]).append(audit)
    document['review']['flags'].append('Połączono fizycznie złączone części dymków; zachowano dotychczasowe obszary i kolejność pierwszej części')
    return document
