"""Conservative safeguards against tracing artwork and overlapping utterances."""
import math
import re
import cv2
import numpy as np
from .geometry import area, intersection, rectangle


def text_bounds(texts):
    return [min(t['box'][0] for t in texts), min(t['box'][1] for t in texts),
            max(t['box'][2] for t in texts), max(t['box'][3] for t in texts)]


def free_text_artwork_guard(image, bubble, texts, checker):
    """Use independent text evidence before replacing a mask that follows artwork.

    A nonuniform interior alone cannot reject a transparent/coloured balloon.
    Require confident free-text labels, a noncompact contour, a nonuniform
    interior outside recognised letters and proof that every OCR line fits the
    smaller text area. The reading anchor and number of utterances stay intact.
    """
    if (not bubble.get('polygons') or not texts or not checker
            or not all(t.get('label')==2 and t.get('score',0)>=.85 for t in texts)):
        return bubble, None
    from .textcheck import pixel_box
    bounds=pixel_box(bubble,image.size)
    rgb=np.asarray(image.crop(bounds))
    if not rgb.size or rgb.shape[0]*rgb.shape[1]>8_000_000:
        return bubble,None
    polys=_polygons(bubble,*image.size,bounds[:2])
    hull=cv2.convexHull(np.concatenate(polys))
    solidity=sum(cv2.contourArea(p) for p in polys)/max(1,cv2.contourArea(hull))
    if solidity>=.94:
        return bubble,None
    target=rectangle(text_bounds(texts),*image.size,bubble['confidence'],'text',margin=6)
    target_box=pixel_box(target,image.size)
    if area(target_box)>=.8*area(bounds):
        return bubble,None
    rows=checker.read(image.crop(bounds))
    valid=[r for r in rows if r.get('score',0)>=.75 and r.get('box')]
    if (not valid or any(not r.get('box') for r in rows)
            or not any(r['score']>=.85 and sum(c.isalpha() for c in r['text'])>=3 for r in valid)):
        return bubble,None
    mask=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillPoly(mask,polys,1)
    inside=cv2.erode(mask,np.ones((7,7),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)
    letters=np.zeros_like(mask)
    for row in rows:
        if not row.get('box'):
            return bubble,None
        a,b,c,d=row['box']
        if not all(math.isfinite(v) for v in (a,b,c,d)) or not (0<=a<c<=1 and 0<=b<d<=1):
            return bubble,None
        # Include even weak OCR lines in the coverage gate: uncertainty must
        # never become permission to crop a possibly genuine word away.
        ocr_box=[bounds[0]+a*rgb.shape[1],bounds[1]+b*rgb.shape[0],
                 bounds[0]+c*rgb.shape[1],bounds[1]+d*rgb.shape[0]]
        if intersection(ocr_box,target_box)/max(1,area(ocr_box))<.995:
            return bubble,None
        x1,y1=max(0,int(a*rgb.shape[1])-2),max(0,int(b*rgb.shape[0])-2)
        x2,y2=min(rgb.shape[1],int(c*rgb.shape[1])+3),min(rgb.shape[0],int(d*rgb.shape[0])+3)
        letters[y1:y2,x1:x2]=1
    text_pixels=rgb[(letters>0)&(inside>0)]
    outside=(inside>0)&(letters==0)
    outside_count=np.count_nonzero(outside)
    if len(text_pixels)<30 or outside_count<100 or outside_count<.35*np.count_nonzero(inside):
        return bubble,None
    # Try several prevalent colours. Large letters can dominate a tight OCR
    # rectangle; assuming its most common colour is paper breaks dark balloons.
    quant=text_pixels.astype(np.int32)//16
    codes=quant[:,0]*256+quant[:,1]*16+quant[:,2]
    values,counts=np.unique(codes,return_counts=True)
    purity=0.0
    for index in np.argsort(counts)[-3:]:
        color=np.median(text_pixels[codes==values[index]],axis=0)
        purity=max(purity,float(np.mean(np.max(np.abs(rgb[outside].astype(np.int16)-color),axis=1)<32)))
    # White artwork (a car or the empty background around figures) can agree
    # with the text paper. A noncompact mask of confidently detected free text
    # still needs an outline: clipped page-edge backgrounds with only partial
    # edge support are not evidence of a physical balloon.
    criterion='nonuniform-interior'
    support=None
    if purity>=.90:
        from .refinement import boundary_support
        touches_page=(bounds[0]==0 or bounds[1]==0 or bounds[2]==image.width or bounds[3]==image.height)
        support=boundary_support(mask,image.crop(bounds)) if touches_page else 1.0
        if not touches_page or not .70<=support<.90:
            return bubble,None
        criterion='page-edge-background-without-supported-outline'
    # Return a new region; preserve the original in diagnostics for editorial
    # recovery, never overwrite hand-verified package data.
    return target,{'reason':'free-text-mask-followed-artwork','box':list(target_box),
                   'solidity':round(float(solidity),4),'background_agreement':round(purity,4),
                   'criterion':criterion,'boundary_support':round(support,4) if support is not None else None,
                   'ocr_lines_preserved':len(rows),'original_region':dict(bubble)}


def region_guard(image, bubble, texts, panels, checker, method):
    """Keep named labels and whole-panel thoughts as text, not invented balloons."""
    if not checker or not texts:
        return bubble, None
    guarded,audit=free_text_artwork_guard(image,bubble,texts,checker)
    if audit:
        return guarded,audit
    bounds=text_bounds(texts)
    b=[bubble['x']*image.width,bubble['y']*image.height,
       (bubble['x']+bubble['w'])*image.width,(bubble['y']+bubble['h'])*image.height]
    frame=any(intersection(b,p['box'])/max(1,area(b)+area(p['box'])-intersection(b,p['box']))>.85 for p in panels)
    # Only inspect suspect/oversized contours; ordinary balloons retain geometry.
    if not frame and method!='text-fallback' and area(b)/max(1,area(bounds))<2.5:
        return bubble,None
    rows=checker.read(image.crop(tuple(map(int,bounds))))
    text=' '.join(row['text'] for row in rows if row['score']>=.85).strip()
    words=re.findall(r'[^\W\d_]+',text,re.UNICODE)
    named=(1<len(words)<=3 and all(w[0].isupper() and len(w)>1 and w[1:].islower() for w in words)
           and not any(c in text for c in '.!?…'))
    from .textcheck import EFFECT_WORDS
    effect=bool(words) and all(w.casefold() in EFFECT_WORDS for w in words)
    if method=='text-fallback' and effect:
        return None,{'reason':'probable-effect-without-contour','ocr':rows,'box':bounds}
    if bubble.get('polygons') and (frame or named):
        return rectangle(bounds,*image.size,bubble['confidence'],'text',margin=6), {
            'reason':'panel-sized-text' if frame else 'possible-name-label','ocr':rows,'box':bounds}
    return bubble,None


def _polygons(b,width,height,origin=(0,0)):
    return [np.rint([[(b['x']+p['x']*b['w'])*width-origin[0],
                     (b['y']+p['y']*b['h'])*height-origin[1]] for p in polygon]).astype(np.int32)
            for polygon in b.get('polygons',[])]


def overlap_share(a,b,width,height):
    x=max(a['x'],b['x'])*width; y=max(a['y'],b['y'])*height
    right=min(a['x']+a['w'],b['x']+b['w'])*width
    bottom=min(a['y']+a['h'],b['y']+b['h'])*height
    if right<=x or bottom<=y:
        return 0
    x,y=math.floor(x),math.floor(y)
    w,h=math.ceil(right)-x+1,math.ceil(bottom)-y+1
    mask_a=np.zeros((h,w),np.uint8);mask_b=np.zeros_like(mask_a)
    pa,pb=_polygons(a,width,height),_polygons(b,width,height)
    total_a=sum(cv2.contourArea(p) for p in pa);total_b=sum(cv2.contourArea(p) for p in pb)
    cv2.fillPoly(mask_a,_polygons(a,width,height,(x,y)),1)
    cv2.fillPoly(mask_b,_polygons(b,width,height,(x,y)),1)
    return np.count_nonzero(mask_a & mask_b)/max(1,min(total_a,total_b))


def guard_conflicts(bubbles,width,height):
    """Do not publish mutually overlapping masks as separately perfect contours.

    Text rectangles preserve every utterance and original ordering; all rejected
    outlines are retained in diagnostics so the editor/research can recover them.
    """
    conflicts=[];suspect=set()
    for i,a in enumerate(bubbles):
        if not a.get('polygons'): continue
        for j in range(i+1,len(bubbles)):
            b=bubbles[j]
            if not b.get('polygons'): continue
            overlap=overlap_share(a,b,width,height)
            if overlap>.08:
                suspect.update((i,j))
                conflicts.append({'regions':[i+1,j+1],'overlap_share':round(float(overlap),4)})
    originals=[]
    for index in sorted(suspect):
        b=bubbles[index]
        originals.append({'index':index+1,'region':dict(b)})
        anchor=b.get('_reading_box',b)
        bounds=[anchor['x']*width,anchor['y']*height,(anchor['x']+anchor['w'])*width,(anchor['y']+anchor['h'])*height]
        bubbles[index]=dict(rectangle(bounds,width,height,b['confidence'],'text',margin=6),_reading_box=anchor)
    return {'pairs':conflicts,'original_contours':originals}
