"""Prototype physical thin white bridges, without annotation input."""
import cv2,numpy as np
from collections import deque
from .geometry import rectangle,contour_box,padded_box
from .quality_guard import _polygons
from .textcheck import pixel_box

def skeleton(binary):
 work=binary.copy();out=np.zeros_like(work);kernel=cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
 if np.all(work):return out
 while np.any(work):
  eroded=cv2.erode(work,kernel);opened=cv2.dilate(eroded,kernel);out|=work&~opened;work=eroded
 return out

def bridge_candidates(image,doc):
 from PIL import Image
 preview=image.copy();preview.thumbnail((1800,1800),resample=Image.Resampling.NEAREST);scale=image.width/preview.width;rgb=np.asarray(preview);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);size=preview.size;old={};eligible={};anchors=doc['analysis'].get('reading_anchors',{});bubbles=doc['result']['bubbles']
 for b in bubbles:
  a=anchors.get(b['id']);matches=[]
  if not a or b.get('type') not in {'bubble','text'}:continue
  for diag in doc['analysis'].get('balloons',[]):
   ts=diag.get('supporting_texts',[])
   if not ts or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in ts):continue
   box=[min(t['box'][0] for t in ts),min(t['box'][1] for t in ts),max(t['box'][2] for t in ts),max(t['box'][3] for t in ts)];r=rectangle(box,*image.size,1,margin=0)
   if all(abs(r[k]-a[k])<1e-6 for k in ('x','y','w','h')):matches.append(ts)
  if len(matches)!=1:continue
  mask=np.zeros(gray.shape,np.uint8)
  if b.get('polygons'):cv2.fillPoly(mask,_polygons(b,*size,(0,0)),1)
  else:
   xx,yy,xxx,yyy=pixel_box(b,size);mask[yy:yyy,xx:xxx]=1
  old[b['id']]=mask;eligible[b['id']]=b
 if len(old)<2:return []
 union=np.maximum.reduce(list(old.values()));stages=[]
 for threshold in (210,240):
  white=(gray>threshold).astype(np.uint8);dt=cv2.distanceTransform(white,cv2.DIST_L2,5);sk=skeleton(white);thin=(cv2.dilate(sk,np.ones((3,3),np.uint8))>0)&(dt<=max(3,12/scale))&(white>0);allowed=(thin|((white>0)&(union>0))).astype(np.uint8)
  _,labels,stats,_=cv2.connectedComponentsWithStats(allowed,8);groups={}
  for bid,b in eligible.items():
   votes=labels[cv2.erode(old[bid],np.ones((3,3),np.uint8))>0];v,n=np.unique(votes,return_counts=True);valid=[(hits,int(k)) for k,hits in zip(v,n) if k and hits>len(votes)*.25]
   if valid:groups.setdefault(max(valid)[1],[]).append(bid)
  result={}
  for idx,ids in groups.items():
   if len(ids)<2 or len({eligible[i].get('panel_id') for i in ids})!=1:continue
   ids=tuple(sorted(ids));result[ids]=(labels==idx,dt,white)
  stages.append(result)
 outputs=[]
 for ids,(component,dt,white) in stages[0].items():
  if ids not in stages[1]:continue
  component&=stages[1][ids][0]
  # Find only the short white paths connecting the actual existing bodies.
  points=np.argwhere(np.maximum.reduce([old[i] for i in ids])>0);y1,x1=points.min(axis=0);y2,x2=points.max(axis=0);pad=max(25,int(max(x2-x1,y2-y1)*.2));x1=max(0,x1-pad);y1=max(0,y1-pad);x2=min(gray.shape[1],x2+pad+1);y2=min(gray.shape[0],y2+pad+1);allowed=component[y1:y2,x1:x2];h,w=allowed.shape;parents=np.full(h*w,-1,np.int32);bodies=[old[i][y1:y2,x1:x2]>0 for i in ids];sources=np.flatnonzero(bodies[0]&allowed);parents[sources]=-2;queue=deque(sources.tolist());goals=np.zeros(h*w,np.int16)
  for n,b in enumerate(bodies[1:],1):goals[(b&allowed).reshape(-1)]=n
  found={};flat=allowed.reshape(-1)
  while queue and len(found)<len(ids)-1:
   p=queue.popleft();g=int(goals[p])
   if g and g not in found:found[g]=p
   yy,xx=divmod(p,w)
   for dy,dx in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
    a,b=yy+dy,xx+dx
    if not(0<=a<h and 0<=b<w):continue
    v=a*w+b
    if flat[v] and parents[v]==-1:parents[v]=p;queue.append(v)
  if len(found)!=len(ids)-1:continue
  path=set()
  for p in found.values():
   while parents[p]>=0:path.add(p);p=int(parents[p])
  mask=np.maximum.reduce([old[i] for i in ids]).copy();newpath=0
  for p in path:
   yy,xx=divmod(p,w);yy+=y1;xx+=x1
   if union[yy,xx]:continue
   radius=int(np.ceil(dt[yy,xx]))+1;cv2.circle(mask,(xx,yy),radius,1,-1);newpath+=1
  if newpath>max(50,2*np.hypot(x2-x1,y2-y1)):continue
  low_old=np.maximum.reduce([old[i] for i in ids]);guide=cv2.resize(((mask>0)&(low_old==0)).astype(np.uint8),image.size,interpolation=cv2.INTER_NEAREST)
  band=cv2.dilate(guide,np.ones((max(5,int(np.ceil(scale*3)))|1,)*2,np.uint8));full_old=np.zeros((image.height,image.width),np.uint8)
  for i in ids:
   body=eligible[i]
   if body.get('polygons'):cv2.fillPoly(full_old,_polygons(body,*image.size,(0,0)),1)
   else:
    a,b,c,d=pixel_box(body,image.size);full_old[b:d,a:c]=1
  native_white=(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2GRAY)>220).astype(np.uint8);allowed_native=((band>0)|(cv2.erode(full_old,np.ones((3,3),np.uint8))>0))&(native_white>0)
  _,native_labels,_,_=cv2.connectedComponentsWithStats(allowed_native.astype(np.uint8),8);common=None
  for i in ids:
   a,b,c,d=pixel_box(anchors[i],image.size);v,n=np.unique(native_labels[b:d,a:c],return_counts=True);matches={int(k) for k,hits in zip(v,n) if k and hits>(c-a)*(d-b)*.25};common=matches if common is None else common&matches
  if not common:continue
  connector=((band>0)&np.isin(native_labels,list(common))).astype(np.uint8);full=full_old|cv2.dilate(connector,np.ones((5,5),np.uint8))
  region=contour_box(full,(0,0),*image.size,min(eligible[i]['confidence'] for i in ids),epsilon=.1,max_vertices=2048);outputs.append((ids,region,dict(method='thin-white-skeleton-bridge',bridge_pixels=newpath,native_white_connection=True)))
 return outputs

