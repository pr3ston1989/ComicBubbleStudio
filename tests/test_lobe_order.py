import copy
import cv2
import numpy as np
import pytest
from PIL import Image
from tools.bubble_studio.geometry import contour_box,rectangle
from tools.bubble_studio.lobe_order import refine_lobe_order


def example(direction='ltr',panel_id='p1'):
    width,height=800,500;rgb=np.full((height,width,3),80,np.uint8);compound=np.zeros((height,width),np.uint8);reply=np.zeros_like(compound)
    cv2.ellipse(compound,(200,100),(90,55),0,0,360,1,-1);cv2.ellipse(compound,(550,140),(70,55),0,0,360,1,-1);cv2.line(compound,(280,103),(490,139),1,4)
    cv2.ellipse(reply,(200,175),(80,35),0,0,360,1,-1)
    rgb[(compound|reply)>0]=255
    boxes=[[155,163,245,188],[510,120,590,160]]
    ocr=[dict(text='FIRST',score=.99,box=[140/width,80/height,230/width,120/height]),dict(text='LAST',score=.99,box=[510/width,120/height,590/width,160/height]),dict(text='NEIGHBOUR',score=.99,box=[155/width,163/height,245/width,188/height])]
    if direction=='rtl':
        rgb=np.fliplr(rgb).copy();compound=np.fliplr(compound).copy();reply=np.fliplr(reply).copy()
        boxes=[[width-c,b,width-a,d] for a,b,c,d in boxes]
        for row in ocr:a,b,c,d=row['box'];row['box']=[1-c,b,1-a,d]
    bubbles=[];anchors={};diagnostics=[];checks=[]
    for i,(mask,box) in enumerate(zip([reply,compound],boxes),1):
        region=contour_box(mask,(0,0),width,height,.95,epsilon=.1,max_vertices=2048);region.update(id=f'b{i}',order=i,panel_id=panel_id);bubbles.append(region)
        anchor=rectangle(box,width,height,1,margin=0);anchors[region['id']]={k:anchor[k] for k in ('x','y','w','h')}
        diagnostics.append(dict(supporting_texts=[dict(box=box,label=1,score=.95)]));checks.append(dict(region_id=region['id'],box=[0,0,width,height],ocr=ocr if i==2 else [ocr[-1]]))
    doc=dict(result=dict(direction=direction,bubbles=bubbles,panels=[] if panel_id is None else [dict(id=panel_id,x=0,y=0,w=1,h=1)]),analysis=dict(reading_anchors=anchors,balloons=diagnostics,text_check=dict(regions=checks)),review=dict(verified=False,flags=[]))
    return Image.fromarray(rgb),doc


@pytest.mark.parametrize('direction',['ltr','rtl'])
@pytest.mark.parametrize('panel_id',['p1',None])
def test_first_physical_lobe_orders_compound_before_reply_even_when_primary_anchor_is_last_lobe(direction,panel_id):
    image,doc=example(direction,panel_id);old=copy.deepcopy(doc);actual=refine_lobe_order(image,doc)
    assert actual['analysis']['reading_anchors']['b1']==old['analysis']['reading_anchors']['b2']
    assert actual['analysis']['leading_lobe_order']['mapping']==dict(b2='b1',b1='b2')
    assert actual['analysis']['page_context']['original']==old


def test_single_confirmed_lobe_cannot_authorize_reordering():
    image,doc=example();doc['analysis']['text_check']['regions'][1]['ocr']=doc['analysis']['text_check']['regions'][1]['ocr'][1:];old=copy.deepcopy(doc)
    assert refine_lobe_order(image,doc)==old


def test_verified_page_and_nonpaper_artwork_keep_their_order():
    image,doc=example();doc['review']['verified']=True;old=copy.deepcopy(doc)
    assert refine_lobe_order(image,doc)==old
    doc['review']['verified']=False;old=copy.deepcopy(doc)
    assert refine_lobe_order(Image.new('RGB',image.size,(120,120,120)),doc)==old
