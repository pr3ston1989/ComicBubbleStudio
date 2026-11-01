import numpy as np
def trim_paper_margin(image,roi,anchors,bubbles):
 """Remove only blank strips at a panel crop edge, never any text anchor."""
 x,y,xx,yy=roi
 rgb=np.asarray(image.crop(roi));white=(np.min(rgb,axis=2)>235)&(np.ptp(rgb.astype(np.int16),axis=2)<16)
 coords=[x,y,xx,yy];size=(image.width,image.height)
 for axis in (0,1):
  profile=np.mean(white,axis=axis)>.985
  for reverse in (False,True):
   arr=profile[::-1] if reverse else profile;n=0
   for value in arr:
    if not value:break
    n+=1
   if not 1<=n<=max(4,len(arr)*.05):continue
   edge=(2 if axis==0 else 3) if reverse else (0 if axis==0 else 1)
   proposed=coords[edge]+(-n if reverse else n)
   strip=[coords[0],coords[1],coords[2],coords[3]]
   strip[axis]=min(proposed,coords[edge]);strip[axis+2]=max(proposed,coords[edge])
   overlaps=False
   for bubble in bubbles:
    anchor=anchors.get(bubble['id'],bubble)
    ab=[anchor['x']*size[0],anchor['y']*size[1],(anchor['x']+anchor['w'])*size[0],(anchor['y']+anchor['h'])*size[1]]
    if min(ab[2],strip[2])>max(ab[0],strip[0]) and min(ab[3],strip[3])>max(ab[1],strip[1]):overlaps=True;break
   if overlaps:continue
   coords[edge]=proposed
 return tuple(coords)
