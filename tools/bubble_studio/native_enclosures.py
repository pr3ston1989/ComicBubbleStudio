"""Prototype connected balloon recovery from stable, bounded native paper."""
import cv2,numpy as np
from .geometry import rectangle,contour_box,_fill,padded_box
from .textcheck import pixel_box
from .quality_guard import _polygons

def frame_box(image, panel):
 gray=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2GRAY)
 x1,y1,x2,y2=pixel_box(panel,image.size);out=[x1,y1,x2,y2]
 for edge in range(4):
  horizontal=edge in (1,3);coord=out[edge];length=(x2-x1) if horizontal else (y2-y1);radius=max(20,min(50,int(length*.05)))
  if horizontal:
   top=max(0,coord-radius);crop=gray[top:min(image.height,coord+radius+1),x1:x2]
  else:
   top=max(0,coord-radius);crop=gray[y1:y2,top:min(image.width,coord+radius+1)].T
  if crop.size==0:continue
  edges=cv2.Canny(crop.copy(),40,100);lines=cv2.morphologyEx(edges,cv2.MORPH_OPEN,np.ones((1,max(20,int(length*.18))),np.uint8));hits=np.count_nonzero(lines,axis=1)
  if hits.max(initial=0)<length*.25:continue
  positions=np.flatnonzero(hits>=max(length*.25,hits.max()*.9));selected=min(positions,key=lambda i:abs(top+int(i)-coord));out[edge]=top+int(selected)
 if out[2]-out[0]<20 or out[3]-out[1]<20:return pixel_box(panel,image.size)
 return tuple(out)

def enclosure_candidates(image,document,trim_blank=False):
 if document.get('review',{}).get('verified'):return []
 bubbles=document['result']['bubbles'];analysis=document.get('analysis',{});anchors=analysis.get('reading_anchors',{});evidence={}
 for b in bubbles:
  a=anchors.get(b['id']);matches=[]
  if not a:continue
  for diagnostic in analysis.get('balloons',[]):
   rows=diagnostic.get('supporting_texts',[])
   if not rows or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in rows):continue
   bounds=[min(t['box'][0] for t in rows),min(t['box'][1] for t in rows),max(t['box'][2] for t in rows),max(t['box'][3] for t in rows)];r=rectangle(bounds,*image.size,1,margin=0)
   if all(abs(r[k]-a[k])<1e-6 for k in ('x','y','w','h')):matches.append(rows)
  if len(matches)==1:evidence[b['id']]=matches[0]
 rois=[]
 for p in document['result']['panels']:
  a=frame_box(image,p);pad=max(20,min(100,round((a[2]-a[0])*.12)))
  # Lettering can bleed sideways beyond the artwork frame. Keep the native
  # top/bottom cut, but first let the actual curved outline close outside it.
  rois.append(((max(0,a[0]-pad),a[1]+2,min(image.width,a[2]+pad),a[3]-2),True))
  rois.append(((a[0]+2,a[1]+2,a[2]-2,a[3]-2),True))
 if image.width*image.height<=8_000_000:rois.append(((0,0,*image.size),False))
 result=[];seen=set()
 for roi,clipped in dict.fromkeys(rois):
  if (roi[2]-roi[0])*(roi[3]-roi[1])>8_000_000:continue
  if trim_blank:
   from .native_margin import trim_paper_margin
   roi=trim_paper_margin(image,roi,anchors,bubbles)
  gray=cv2.cvtColor(np.asarray(image.crop(roi)),cv2.COLOR_RGB2GRAY);stages=[]
  for threshold in (220,240):
   _,labels,stats,_=cv2.connectedComponentsWithStats((gray>threshold).astype(np.uint8),8);groups={}
   for b in bubbles:
    if b['id'] not in evidence:continue
    a=anchors[b['id']];box=pixel_box(a,image.size);x1,y1=max(0,box[0]-roi[0]),max(0,box[1]-roi[1]);x2,y2=min(gray.shape[1],box[2]-roi[0]),min(gray.shape[0],box[3]-roi[1])
    if x2<=x1 or y2<=y1:continue
    ids,hits=np.unique(labels[y1:y2,x1:x2],return_counts=True);eligible=[(n,int(k)) for k,n in zip(ids,hits) if k and n>.4*(x2-x1)*(y2-y1)]
    if not eligible:continue
    component=max(eligible)[1];groups.setdefault(component,[]).append(b)
   candidates={}
   for component,members in groups.items():
    if len(members)<2 or (not clipped and len({b.get('panel_id') for b in members})!=1):continue
    key=tuple(sorted(b['id'] for b in members));x,y,w,h,_=stats[component]
    if not clipped and (x==0 or y==0 or x+w==gray.shape[1] or y+h==gray.shape[0]):continue
    mask=(_fill((labels==component).astype(np.uint8)*255)>0).astype(np.uint8);count=np.count_nonzero(mask)
    if count<200 or count>gray.size*.75 or (x==0 and x+w==gray.shape[1]) or (y==0 and y+h==gray.shape[0]):continue
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);hull=cv2.convexHull(np.concatenate(contours));solidity=count/max(1,cv2.contourArea(hull))
    if solidity>.97:continue
    candidate=cv2.dilate(mask,np.ones((5,5),np.uint8));valid=True
    for b in members:
     if b.get('polygons'):
      original=np.zeros_like(mask);cv2.fillPoly(original,_polygons(b,*image.size,roi[:2]),1);core=cv2.erode(original,np.ones((5,5),np.uint8))
      if np.count_nonzero((candidate>0)&(core>0))/max(1,np.count_nonzero(core))<.98:valid=False;break
     anchor=pixel_box(anchors[b['id']],image.size);x1,y1=anchor[0]-roi[0],anchor[1]-roi[1];x2,y2=anchor[2]-roi[0],anchor[3]-roi[1]
     if x2<=0 or y2<=0 or x1>=mask.shape[1] or y1>=mask.shape[0] or np.mean(candidate[max(0,y1):min(mask.shape[0],y2),max(0,x1):min(mask.shape[1],x2)])<.8:valid=False;break
    if valid:candidates[key]=(candidate,float(solidity))
   stages.append(candidates)
  for key,(a,solidity) in stages[0].items():
   if key in seen or key not in stages[1]:continue
   b=stages[1][key][0];stability=np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))
   if stability<.99:continue
   mask=a|b
   # Every text anchor inside this physical enclosure must be part of the group.
   bad=False
   for other in bubbles:
    if other['id'] in key:continue
    box=pixel_box(anchors.get(other['id'],other),image.size);x1,y1=max(0,box[0]-roi[0]),max(0,box[1]-roi[1]);x2,y2=min(mask.shape[1],box[2]-roi[0]),min(mask.shape[0],box[3]-roi[1])
    if x2>x1 and y2>y1 and np.any(mask[y1:y2,x1:x2]):bad=True;break
   if bad:continue
   confidence=max(r['confidence'] for r in bubbles if r['id'] in key);region=contour_box(mask,roi,*image.size,confidence)
   result.append((key,region,dict(method='connected-native-paper',stability=stability,solidity=solidity)));seen.add(key)
 return result

