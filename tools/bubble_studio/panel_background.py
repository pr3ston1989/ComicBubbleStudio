"""Experimental native-text repair of a mask that follows a whole panel background."""
import copy
import cv2,numpy as np
from .compound_guard import _texts
from .geometry import rectangle,area,intersection
from .textcheck import pixel_box
from .quality_guard import _polygons

def proposal(image,document,b):
 if not b.get('polygons'):return None
 texts=_texts(image,document,b)
 if not texts or any(t.get('label')!=2 or t.get('score',0)<.90 for t in texts):return None
 panel=next((p for p in document['result'].get('panels',[]) if p['id']==b.get('panel_id')),None)
 if panel is None:return None
 bounds=pixel_box(b,image.size);pb=pixel_box(panel,image.size);pw,ph=pb[2]-pb[0],pb[3]-pb[1]
 aligned=[abs(v-u)<=size*.025 for v,u,size in zip(bounds,pb,(pw,ph,pw,ph))]
 if sum(aligned)<3 or bounds[0]<pb[0]-pw*.025 or bounds[1]<pb[1]-ph*.025 or bounds[2]>pb[2]+pw*.025 or bounds[3]>pb[3]+ph*.025:return None
 crop=image.crop(bounds);crop.thumbnail((900,900));mask=np.zeros((crop.height,crop.width),np.uint8)
 points=[np.rint([[p['x']*crop.width,p['y']*crop.height] for p in poly]).astype(np.int32) for poly in b['polygons']];cv2.fillPoly(mask,points,1)
 hull=cv2.convexHull(np.concatenate(points));solidity=sum(cv2.contourArea(p) for p in points)/max(1,cv2.contourArea(hull))
 if solidity>=.88 or np.mean(mask)<.35:return None
 edge=[np.mean(mask[:3]),np.mean(mask[-3:]),np.mean(mask[:,:3]),np.mean(mask[:,-3:])]
 if sum(v>.30 and aligned[i] for v,i in zip(edge,(1,3,0,2)))<3:return None
 anchor=document['analysis']['reading_anchors'][b['id']];ab=pixel_box(anchor,image.size)
 if area(ab)/max(1,area(bounds)*np.mean(mask))>.25:return None
 check=next((r for r in document['analysis'].get('text_check',{}).get('regions',[]) if r['region_id']==b['id']),None)
 if not check or len(check.get('box',[]))!=4:return None
 x,y,xx,yy=check['box'];native=[];ignored=[];anchors=document['analysis']['reading_anchors']
 for r in check.get('ocr',[]):
  if len(r.get('box',[]))!=4:return None
  a,c,aa,cc=r['box'];box=[x+a*(xx-x),y+c*(yy-y),x+aa*(xx-x),y+cc*(yy-y)]
  if intersection(box,ab)/max(1,area(box))>=.95:native.append(dict(r,box=box));continue
  neighbours=[pixel_box(anchors.get(other['id'],other),image.size) for other in document['result']['bubbles'] if other['id']!=b['id']]
  if any(intersection(box,other)/max(1,area(box))>=.95 for other in neighbours):ignored.append(dict(r,box=box));continue
  # Any unassigned word, including weak OCR, prevents cropping the mask.
  return None
 if not native or not any(r['score']>=.9 and sum(c.isalpha() for c in r['text'])>=3 for r in native):return None
 box=[min([ab[0]]+[r['box'][0] for r in native]),min([ab[1]]+[r['box'][1] for r in native]),max([ab[2]]+[r['box'][2] for r in native]),max([ab[3]]+[r['box'][3] for r in native])];target=rectangle(box,*image.size,b['confidence'],'text',margin=6)
 targetbox=pixel_box(target,image.size)
 if any(intersection(targetbox,pixel_box(anchors.get(other['id'],other),image.size))/max(1,area(pixel_box(anchors.get(other['id'],other),image.size)))>.01 for other in document['result']['bubbles'] if other['id']!=b['id']):return None
 return target,dict(reason='free-text-mask-followed-three-panel-edges',solidity=solidity,panel_edge_shares=list(map(float,edge)),native_ocr=native,neighbour_ocr_ignored=ignored,original_region=copy.deepcopy(b))

def refine(image,document):
 if document.get('review',{}).get('verified'):return document
 changes=[]
 for i,b in enumerate(document['result']['bubbles']):
  proposed=proposal(image,document,b)
  if proposed is None:continue
  target,audit=proposed;target.update({k:b[k] for k in ('id','order','panel_id')});document['result']['bubbles'][i]=target;changes.append(dict(id=b['id'],**audit))
 if changes:
  document['analysis']['panel_background_repair']=dict(changes=changes);document['review']['flags'].append('Ograniczono obszar tekstu bez dymka do jego słów; sprawdź wynik')
 return document
