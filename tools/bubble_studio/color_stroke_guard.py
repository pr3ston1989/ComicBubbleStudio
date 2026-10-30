"""Chromatic ink recovery with the same closure and branch guards as luminance."""
import cv2
import numpy as np
from .geometry import padded_box
from .textcheck import pixel_box
from .quality_guard import _polygons
from .stroke_guard import recover_stroke_outline, recover_page_outlines


def recover_color_stroke(image, bubble, texts):
    if (bubble.get('type')!='bubble' or len(bubble.get('polygons',[]))!=1
            or not texts or not all(t.get('label')==1 and t.get('score',0)>=.7 for t in texts)):
        return bubble,None
    roi=padded_box(pixel_box(bubble,image.size),*image.size,.6,minimum=60)
    if (roi[2]-roi[0])*(roi[3]-roi[1])>6_000_000:
        return bubble,None
    rgb=np.asarray(image.crop(roi));mask=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillPoly(mask,_polygons(bubble,*image.size,roi[:2]),1)
    band=(cv2.dilate(mask,np.ones((9,9),np.uint8))>0)&(cv2.erode(mask,np.ones((3,3),np.uint8))==0)
    pixels=rgb[band]
    if not len(pixels):return bubble,None
    quant=pixels.astype(np.int32)//16;codes=quant[:,0]*256+quant[:,1]*16+quant[:,2]
    values,counts=np.unique(codes,return_counts=True)
    for idx in np.argsort(counts)[-4:][::-1]:
        if counts[idx]<len(pixels)*.03:continue
        color=np.median(pixels[codes==values[idx]],axis=0).astype(np.int16)
        result,audit=recover_stroke_outline(image,bubble,texts,ink_color=color)
        if audit is not None:
            return result,dict(audit,color=color.tolist())
    return bubble,None


def recover_page_color_outlines(image,document):
    return recover_page_outlines(image,document,recovery=recover_color_stroke,
        audit_key='color_stroke_recovery',flag='Uzupełniono obrys na podstawie koloru zamkniętej linii dymka; sprawdź podgląd')
