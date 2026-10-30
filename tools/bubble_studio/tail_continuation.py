"""Continue an existing tapered tail only along stable, terminating image ink."""
import cv2,numpy as np
from .geometry import padded_box,contour_box
from .quality_guard import _polygons
from .textcheck import pixel_box

def recover_tail_continuation(image,bubble,texts):
 if (bubble.get('type')!='bubble' or len(bubble.get('polygons',[]))!=1 or not texts
     or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in texts)):return bubble,None
 bounds=pixel_box(bubble,image.size);short=min(bounds[2]-bounds[0],bounds[3]-bounds[1]);roi=padded_box(bounds,*image.size,.75,minimum=100)
 if (roi[2]-roi[0])*(roi[3]-roi[1])>6_000_000:return bubble,None
 rgb=np.asarray(image.crop(roi));old=np.zeros(rgb.shape[:2],np.uint8);cv2.fillPoly(old,_polygons(bubble,*image.size,roi[:2]),1);count=np.sum(old);k=max(9,round(short*.18))|1;opened=cv2.morphologyEx(old,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k)));dist=cv2.distanceTransform(1-opened,cv2.DIST_L2,5);fragments=old&(1-opened);_,labels,stats,_=cv2.connectedComponentsWithStats(fragments,8);yy,xx=np.indices(old.shape,dtype=np.float32)
 for idx,(x,y,w,h,area) in enumerate(stats[1:],1):
  if area<8 or area>count*.15:continue
  component=labels==idx;reach=float(dist[component].max())
  if reach<max(7,short*.04):continue
  points=np.argwhere(component&(dist>=reach*.55))[:,::-1].astype(np.float32)
  if len(points)<5:continue
  center=points.mean(axis=0);_,_,vt=np.linalg.svd(points-center,full_matrices=False);axis=vt[0];root=np.argwhere(component&(dist<reach*.25))[:,::-1]
  if not len(root):continue
  root=root.mean(axis=0)
  if np.dot(axis,center-root)<0:axis=-axis
  perp=np.array([-axis[1],axis[0]]);projection=(points-center)@axis;tip=points[np.argmax(projection)];maxreach=min(short*.95,max(short*.12,reach*2.5));along=(xx-tip[0])*axis[0]+(yy-tip[1])*axis[1];across=(xx-tip[0])*perp[0]+(yy-tip[1])*perp[1];halfwidth=max(3,short*.035)+np.maximum(0,along)*.12;cone=(along>=-max(3,short*.04))&(along<=maxreach)&(np.abs(across)<=halfwidth);contact=((xx-tip[0])**2+(yy-tip[1])**2<=max(4,short*.05)**2)&cone
  local=rgb[((xx-tip[0])**2+(yy-tip[1])**2<=max(6,short*.105)**2)&(cv2.dilate(old,np.ones((7,7),np.uint8))>0)];quant=local.astype(np.int32)//16;codes=quant[:,0]*256+quant[:,1]*16+quant[:,2];values,hits=np.unique(codes,return_counts=True)
  for n in np.argsort(hits)[-5:][::-1]:
   if hits[n]<len(local)*.03:continue
   color=np.median(local[codes==values[n]],axis=0);stages=[]
   paper=np.median(rgb[cv2.erode(old,np.ones((7,7),np.uint8))>0],axis=0)
   if np.max(np.abs(color-paper))<60:continue
   for tolerance in (12,24):
    ink=((np.max(np.abs(rgb.astype(np.int16)-color),axis=2)<=tolerance)&cone).astype(np.uint8);_,ls,st,_=cv2.connectedComponentsWithStats(ink,8);ids,hc=np.unique(ls[contact],return_counts=True);choices=[]
    for lab,touches in zip(ids,hc):
     if not lab or touches<2:continue
     piece=ls==lab;added=piece&(old==0);forward=added&(along>max(1,short*.018))
     if np.count_nonzero(forward)<5:continue
     if np.count_nonzero(piece&(old>0))<3:continue
     if np.any(forward[0]) or np.any(forward[-1]) or np.any(forward[:,0]) or np.any(forward[:,-1]):continue
     end=float(along[forward].max());distance=cv2.distanceTransform(1-old,cv2.DIST_L2,5);extension=float(distance[added].max());thickness=float(cv2.distanceTransform(added.astype(np.uint8),cv2.DIST_L2,5).max())*2
     if extension<7 or end>=maxreach-max(1,short*.018) or np.any(forward&(np.abs(across)>=halfwidth-max(1,short*.006))) or thickness>max(12,short*.08) or np.sum(added)>count*.12:continue
     widths=[]
     for step in range(max(1,int(end))):
      cross=across[piece&(along>=step)&(along<step+1)]
      widths.append(float(cross.max()-cross.min()+1) if len(cross) else 0)
     early=[v for v in widths[max(0,int(end*.1)):max(1,int(end*.4))] if v];late=[v for v in widths[max(0,int(end*.6)):max(1,int(end*.95))] if v]
     if not early or not late or np.median(late)>.90*np.median(early) or max(late)>max(early)*1.1:continue
     merged=old|piece.astype(np.uint8);cs,_=cv2.findContours(merged,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
     if len([c for c in cs if cv2.contourArea(c)>=12])!=1:continue
     filled=np.zeros_like(old);cv2.drawContours(filled,cs,-1,1,-1);delta=(filled>0)&(old==0)
     face=across[(old>0)&(along>=-max(3,short*.045))&(along<=-max(1,short*.006))]
     width=float(face.max()-face.min()) if len(face) else 0
     if np.sum(delta)>count*.15 or width>max(4,short*.06) and np.count_nonzero(delta&~piece)<max(8,np.sum(delta)*.15):continue
     choices.append((extension,filled,delta,dict(reach=extension,thickness=thickness,end=end)))
    if not choices:break
    stages.append(max(choices,key=lambda p:p[0]))
   if len(stages)!=2:continue
   a,b=stages;stability=np.sum(a[2]&b[2])/max(1,np.sum(a[2]|b[2]))
   if stability<.80 or abs(a[3]['end']-b[3]['end'])>max(2,short*.018):continue
   result=contour_box(a[1],roi,*image.size,bubble['confidence'],epsilon=.1,max_vertices=2048);result.update({k:bubble[k] for k in ('id','order','panel_id') if k in bubble})
   if len(result['polygons'])!=1:continue
   check=np.zeros_like(old);cv2.fillPoly(check,_polygons(result,*image.size,roi[:2]),1)
   if np.sum(check&old)/max(1,count)<.999:continue
   return result,dict(a[3],method='native-directional-tail',branch_stability=float(stability),old_tail_length=reach,color=color.tolist(),mask_preserved=float(np.sum(check&old)/max(1,count)))
 return bubble,None



def continue_page_tails(image,document):
 from .stroke_guard import recover_page_outlines
 return recover_page_outlines(image,document,recovery=recover_tail_continuation,audit_key='tail_continuation',flag='Uzupełniono zwężającą się końcówkę zgodnie z linią na obrazie; sprawdź obrys')
