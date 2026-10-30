import copy
import cv2
import numpy as np
import pytest
from PIL import Image
from tools.bubble_studio.geometry import contour_box, rectangle
from tools.bubble_studio.thought_dots import recover_thought_dots,recover_page_thought_dots


def example(scale=1, flipped=False, kind='circles', shade=255, witness=False):
    width=height=round(500*scale);rgb=np.full((height,width,3),180,np.uint8);mask=np.zeros((height,width),np.uint8)
    point=lambda p:tuple(round(v*scale) for v in p)
    cv2.ellipse(rgb,point((250,170)),point((100,75)),0,0,360,(255,255,255),-1)
    cv2.ellipse(rgb,point((250,170)),point((100,75)),0,0,360,(0,0,0),max(1,round(3*scale)))
    cv2.ellipse(mask,point((250,170)),point((100,75)),0,0,360,1,-1)
    for i,(cx,cy,radius) in enumerate([(290,258,12),(305,285,8)]):
        if kind=='single' and i:continue
        if kind=='windows':
            a,b=point((cx-radius,cy-radius)),point((cx+radius,cy+radius));cv2.rectangle(rgb,a,b,(0,0,0),-1);inset=round(3*scale);cv2.rectangle(rgb,(a[0]+inset,a[1]+inset),(b[0]-inset,b[1]-inset),(shade,)*3,-1)
        else:
            cv2.circle(rgb,point((cx,cy)),round(radius*scale),(0,0,0),-1);cv2.circle(rgb,point((cx,cy)),round((radius-3)*scale),(shade,)*3,-1)
        if witness and i==0:cv2.circle(mask,point((cx,cy)),round(radius*scale),1,-1)
    if flipped:rgb=np.fliplr(rgb).copy();mask=np.fliplr(mask).copy()
    bubble=contour_box(mask,(0,0),width,height,.95,epsilon=.1,max_vertices=2048);bubble.update(id='b1',order=1,panel_id='p1')
    row=dict(box=[200*scale,140*scale,300*scale,190*scale],label=1,score=.95)
    return Image.fromarray(rgb),bubble,[row]


@pytest.mark.parametrize('scale',[1,1.5,2])
@pytest.mark.parametrize('flipped',[False,True])
def test_native_thought_chain_preserves_body_across_scale_and_reflection(scale,flipped):
    image,bubble,rows=example(scale,flipped);region,audit=recover_thought_dots(image,bubble,rows)
    assert audit and len(audit['circles'])==2 and audit['mask_preserved']>=.999
    assert region['id']==bubble['id'] and region['order']==bubble['order']


@pytest.mark.parametrize('kind,shade',[('single',255),('windows',255),('circles',230)])
def test_single_circle_rectangular_windows_and_unstable_white_are_rejected(kind,shade):
    image,bubble,rows=example(kind=kind,shade=shade)
    assert recover_thought_dots(image,bubble,rows)==(bubble,None)


def test_existing_root_circle_can_confirm_a_missing_second_circle():
    image,bubble,rows=example(witness=True)
    assert recover_thought_dots(image,bubble,rows)[1]


def test_weak_or_free_text_cannot_authorize_circle_recovery():
    image,bubble,rows=example();rows[0]['score']=.6
    assert recover_thought_dots(image,bubble,rows)==(bubble,None)
    rows[0]['score']=.95;bubble['type']='text'
    assert recover_thought_dots(image,bubble,rows)==(bubble,None)


def test_verified_page_and_neighbouring_anchor_are_protected():
    image,bubble,rows=example();anchor=rectangle(rows[0]['box'],*image.size,1,margin=0)
    doc=dict(result=dict(bubbles=[bubble]),analysis=dict(reading_anchors=dict(b1={k:anchor[k] for k in ('x','y','w','h')}),balloons=[dict(supporting_texts=rows)]),review=dict(flags=[],verified=True))
    old=copy.deepcopy(doc);assert recover_page_thought_dots(image,doc)==old
    doc['review']['verified']=False;other=rectangle([297,277,313,293],*image.size,.9,'text',margin=0);other.update(id='b2',order=2)
    doc['result']['bubbles'].append(other);doc['analysis']['reading_anchors']['b2']={k:other[k] for k in ('x','y','w','h')};old=copy.deepcopy(doc)
    assert recover_page_thought_dots(image,doc)==old
