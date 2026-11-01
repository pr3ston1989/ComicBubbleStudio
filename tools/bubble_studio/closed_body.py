"""Recover compact white balloon bodies after segmentation leaks into a panel.

Only closed native-paper components are considered. Original text anchors,
owned OCR words and the complete reading sequence are immutable.
"""
import copy,math,re
from collections import Counter
import cv2,numpy as np
from .compound_guard import _texts
from .native_enclosures import frame_box
from .native_margin import trim_paper_margin
from .geometry import rectangle,contour_box,padded_box,area,intersection,_fill
from .quality_guard import _polygons
from .textcheck import pixel_box
from .refinement import boundary_support
def compact(s):return ''.join(c.casefold() for c in s if c.isalnum())
def own_ocr(document,b,size):
 anchor=document['analysis'].get('reading_anchors',{}).get(b['id'])
 if not anchor:return None
 ab=pixel_box(anchor,size);check=next((r for r in document['analysis'].get('text_check',{}).get('regions',[]) if r['region_id']==b['id']),None)
 if not check or len(check.get('box',[]))!=4:return None
 x,y,xx,yy=check['box'];inside=[];outside=[]
 for r in check.get('ocr',[]):
  if len(r.get('box',[]))!=4:return None
  a,c,aa,cc=r['box'];box=[x+a*(xx-x),y+c*(yy-y),x+aa*(xx-x),y+cc*(yy-y)]
  record=dict(r,box=box)
  if intersection(box,ab)/max(1,area(box))>=.5:inside.append(record)
  else:outside.append(record)
 if not any(r.get('score',0)>=.90 and sum(c.isalnum() for c in r.get('text',''))>=3 for r in inside):return None
 return anchor,ab,inside,outside
def raster(b,size,roi):
 out=np.zeros((roi[3]-roi[1],roi[2]-roi[0]),np.uint8)
 if b.get('polygons'):cv2.fillPoly(out,_polygons(b,*size,roi[:2]),1)
 else:
  x,y,xx,yy=pixel_box(b,size);out[max(0,y-roi[1]):min(out.shape[0],yy-roi[1]),max(0,x-roi[0]):min(out.shape[1],xx-roi[0])]=1
 return out
def text_safe(image,document,target,ab,inside,checker):
 tb=pixel_box(target,image.size)
 neighbours=[pixel_box(document['analysis']['reading_anchors'].get(o['id'],o),image.size) for o in document['result']['bubbles'] if o['id']!=target['id']]
 if any(intersection(tb,n)/max(1,area(n))>.01 for n in neighbours):return None
 mask=raster(target,image.size,tb)
 for box in [ab]+[r['box'] for r in inside]:
  if intersection(box,tb)/max(1,area(box))<.995:return None
  x,y,xx,yy=box
  x,y=max(0,int(math.floor(x-tb[0]))),max(0,int(math.floor(y-tb[1])));xx,yy=min(mask.shape[1],int(math.ceil(xx-tb[0]))),min(mask.shape[0],int(math.ceil(yy-tb[1])))
  if xx<=x or yy<=y or np.mean(mask[y:yy,x:xx])<.995:return None
 actual=checker.read(image.crop(tb));reliable=[r for r in actual if r.get('score',0)>=.85]
 source=' '.join(r['text'] for r in inside if r.get('score',0)>=.85)
 reread=' '.join(r['text'] for r in reliable)
 sc,ac=Counter(compact(source)),Counter(compact(reread));common=sum((sc&ac).values())
 if not sc or not ac or common/sum(sc.values())<.65 or common/sum(ac.values())<.90:return None
 for r in actual:
  if len(r.get('box',[]))!=4:return None
  a,c,aa,cc=r['box'];x,y=int(a*mask.shape[1]),int(c*mask.shape[0]);xx,yy=int(math.ceil(aa*mask.shape[1])),int(math.ceil(cc*mask.shape[0]))
  if xx<=x or yy<=y or np.mean(mask[y:yy,x:xx])<.995:return None
 preserved=[]
 for row in inside:
  a,c,aa,cc=row['box'];preserved.append(dict(row,box=[(a-tb[0])/(tb[2]-tb[0]),(c-tb[1])/(tb[3]-tb[1]),(aa-tb[0])/(tb[2]-tb[0]),(cc-tb[1])/(tb[3]-tb[1])]))
 return dict(region_id=target['id'],box=list(tb),ocr=preserved,uncertain=any(r.get('score',0)<.75 for r in preserved),independent_reread=actual)
def propose(image,document,b,checker):
 if document.get('review',{}).get('verified') or not b.get('polygons'):return []
 texts=_texts(image,document,b)
 if not texts or any(t.get('score',0)<.90 or t.get('label')!=1 for t in texts):return []
 evidence=own_ocr(document,b,image.size)
 if evidence is None:return []
 anchor,ab,inside,outside=evidence;bb=pixel_box(b,image.size);has_contour=bool(b.get('polygons'));outputs=[]
 # Unassigned words cannot be discarded as decoration merely by visual vote.
 neighbours=[pixel_box(document['analysis']['reading_anchors'].get(o['id'],o),image.size) for o in document['result']['bubbles'] if o['id']!=b['id']]
 if any(r.get('score',0)>=.85 and sum(c.isalnum() for c in r.get('text',''))>=3 and not any(intersection(r['box'],n)/max(1,area(r['box']))>=.5 for n in neighbours) for r in outside):return []
 panel_for_body=next((p for p in document['result'].get('panels',[]) if p['id']==b.get('panel_id')),None)
 if panel_for_body is None:return []
 frame=frame_box(image,panel_for_body)
 edge_count=sum(abs(a-c)<=length*.03 for a,c,length in zip(bb,frame,(frame[2]-frame[0],frame[3]-frame[1],frame[2]-frame[0],frame[3]-frame[1])))
 if edge_count<2:return []
 if has_contour:
  initial=raster(b,image.size,bb);ax,ay,axx,ayy=ab;ix,iy=max(0,ax-bb[0]),max(0,ay-bb[1]);jx,jy=min(initial.shape[1],axx-bb[0]),min(initial.shape[0],ayy-bb[1])
  if jx<=ix or jy<=iy or np.sum(initial[iy:jy,ix:jx])/max(1,area(ab))<.90:return []
  roi=bb;mask=raster(b,image.size,roi);contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);hull=cv2.convexHull(np.concatenate(contours));solidity=np.count_nonzero(mask)/max(1,cv2.contourArea(hull))
  panel=next((p for p in document['result'].get('panels',[]) if p['id']==b.get('panel_id')),None)
  aligned=0
  if panel:
   pb=pixel_box(panel,image.size);aligned=sum(abs(a-c)<=size*.03 for a,c,size in zip(bb,pb,(pb[2]-pb[0],pb[3]-pb[1],pb[2]-pb[0],pb[3]-pb[1])))
  # Compact masks may also miss a real body; native border and visual checks decide.
 else:solidity=None;aligned=0;panel=None
 # A real closed paper component is an independent alternative to a SAM mask.
 if all(t.get('label')==1 for t in texts):
  rois=[(padded_box(bb,*image.size,p,minimum=25),False) for p in ([.25,.65,1.2] if has_contour else [.7,1.6,3.0])]
  if panel is not None:
   pb=frame_box(image,panel)
   if intersection(ab,pb)/max(1,area(ab))>=.995:
    clipped=(pb[0]+2,pb[1]+2,pb[2]-2,pb[3]-2)
    clipped=trim_paper_margin(image,clipped,document['analysis']['reading_anchors'],document['result']['bubbles'])
    rois.append((clipped,True))
  largest=max(3,min(9,int(min(image.size)*.003)//2*2+1))
  rois=[(roi,physical,closing) for roi,physical in rois for closing in [0]+list(range(3,largest+1,2))]
  for roi,physical,closing in rois:
   if area(roi)>6_000_000 or min(roi[2]-roi[0],roi[3]-roi[1])<8:continue
   gray=cv2.cvtColor(np.asarray(image.crop(roi)),cv2.COLOR_RGB2GRAY);masks=[]
   for threshold in (220,240):
    paper=(gray>threshold).astype(np.uint8)
    if closing:paper=1-cv2.morphologyEx(1-paper,cv2.MORPH_CLOSE,np.ones((closing,closing),np.uint8))
    _,labels,stats,_=cv2.connectedComponentsWithStats(paper,8)
    x,y,xx,yy=ab[0]-roi[0],ab[1]-roi[1],ab[2]-roi[0],ab[3]-roi[1]
    if min(x,y)<0 or xx>gray.shape[1] or yy>gray.shape[0]:break
    values,counts=np.unique(labels[y:yy,x:xx],return_counts=True);valid=[(n,int(k)) for k,n in zip(values,counts) if k and n>.4*area(ab)]
    if not valid:break
    k=max(valid)[1];a,c,w,h,_=stats[k]
    if not physical and (a==0 or c==0 or a+w>=gray.shape[1] or c+h>=gray.shape[0]):break
    m=(_fill((labels==k).astype(np.uint8)*255)>0).astype(np.uint8);m=cv2.dilate(m,np.ones((5,5),np.uint8))
    if np.mean(m)>.72 or np.mean(m[y:yy,x:xx])<.995:break
    masks.append(m)
   if len(masks)!=2 or np.count_nonzero(masks[0]&masks[1])/max(1,np.count_nonzero(masks[0]|masks[1]))<.99:continue
   m=masks[0]|masks[1];count=np.count_nonzero(m)
   if has_contour:
    oldmask=raster(b,image.size,roi);oldcount=np.count_nonzero(oldmask);union=np.count_nonzero(m|oldmask);common=np.count_nonzero(m&oldmask)
    if not 1.1*area(ab)<count<4*oldcount or (common/max(1,oldcount)<.20 and common/max(1,count)<.90):continue
    if common/max(1,union)>.88:continue
   elif not 1.1*area(bb)<count<8*area(ab):continue
   support=boundary_support(m*255,image.crop(roi))
   if not physical and support<.94:continue
   target=contour_box(m,roi,*image.size,b['confidence'],epsilon=.4,max_vertices=1024);target.update({k:b[k] for k in ('id','order','panel_id')})
   check=text_safe(image,document,target,ab,inside,checker)
   if check is None:continue
   outputs.append(dict(kind='native-enclosure',target=target,native_check=check,inside_ocr=inside,outside_ocr=outside,old_solidity=solidity,physical_panel_clip=physical,ink_gap_closing=closing,boundary_support=support));break
 return outputs


def closed_body_proof(image, document, old, new):
    """Require a compact native body nested in a substantial paper spill.

    Native extraction must already have passed both thresholds, ink boundary,
    text coverage and neighbour checks. This gate only permits a shrink when
    the discarded area is predominantly blank paper along the panel edges.
    A shortened thin tail or a merely different acceptable contour cannot pass.
    """
    size = image.size
    before, after = pixel_box(old, size), pixel_box(new, size)
    roi = tuple(min(a, b) if i < 2 else max(a, b)
                for i, (a, b) in enumerate(zip(before, after)))
    old_mask, new_mask = raster(old, size, roi), raster(new, size, roi)
    old_area, new_area = np.count_nonzero(old_mask), np.count_nonzero(new_mask)
    if not old_area or not new_area:
        return None
    contained = float(np.sum(old_mask & new_mask) / new_area)
    contours, _ = cv2.findContours(new_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(np.concatenate(contours))
    solidity = float(new_area / max(1, cv2.contourArea(hull)))
    panel = next((p for p in document['result']['panels']
                  if p['id'] == old.get('panel_id')), None)
    if panel is None:
        return None
    frame = frame_box(image, panel)
    edges = sum(abs(a-c) <= length*.03 for a, c, length in
                zip(before, frame, (frame[2]-frame[0], frame[3]-frame[1],
                                    frame[2]-frame[0], frame[3]-frame[1])))
    removed = (old_mask > 0) & (new_mask == 0)
    removed_area = np.count_nonzero(removed)
    gray = cv2.cvtColor(np.asarray(image.crop(roi)), cv2.COLOR_RGB2GRAY)
    paper = int(np.sum((gray > 240) & removed))
    if not (new_area < old_area and contained >= .985 and solidity >= .94
            and edges >= 2 and paper / old_area >= .10
            and paper / max(1, removed_area) >= .80):
        return None
    return dict(method='closed-native-body-with-panel-paper-spill',
                body_contained_in_old=contained, body_solidity=solidity,
                old_panel_edges=edges, removed_paper_share=paper / old_area,
                removed_area_paper_share=paper / max(1, removed_area))


def refine(image, document, checker):
    """Replace body geometry only, with complete rollback on any failure."""
    if checker is None or document.get('review', {}).get('verified'):
        return document
    original = copy.deepcopy(document)
    changes = []
    try:
        checks = document['analysis'].get('text_check', {}).get('regions', [])
        by_id = {r['region_id']: i for i, r in enumerate(checks)}
        for index, old in enumerate(document['result']['bubbles']):
            for proposal in propose(image, document, old, checker):
                target = proposal['target']
                proof = closed_body_proof(image, document, old, target)
                if proof is None or old['id'] not in by_id:
                    continue
                check_index = by_id[old['id']]
                changes.append(dict(region_id=old['id'], original_region=copy.deepcopy(old),
                    original_text_check=copy.deepcopy(checks[check_index]),
                    proof=proof, threshold_stability_required=.99,
                    ink_gap_closing=proposal['ink_gap_closing'],
                    boundary_support=proposal['boundary_support']))
                document['result']['bubbles'][index] = target
                checks[check_index] = proposal['native_check']
                break
        if changes:
            document['analysis']['native_body_refinement'] = dict(changes=changes)
            document['review']['flags'].append(
                'Odtworzono korpus dymka z obrazu; zachowano tekst i kolejność czytania')
    except Exception as error:
        document = original
        document['analysis']['native_body_error'] = type(error).__name__
        document['review']['flags'].append(
            'Dodatkowa analiza obrysu była niedostępna; zachowano poprzedni wynik')
    return document
