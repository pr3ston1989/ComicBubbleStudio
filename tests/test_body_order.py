import copy
import cv2
import numpy as np
from PIL import Image
from tools.bubble_studio.body_order import refine_body_order
from tools.bubble_studio.geometry import contour_box,rectangle


def document():
    size=(1000,500);bubbles=[];anchors={}
    for i,center,radii,text in [(1,(650,100),(90,70),[600,70,700,110]),(2,(230,180),(110,140),[160,160,300,280])]:
        mask=np.zeros((500,1000),np.uint8);cv2.ellipse(mask,center,radii,0,0,360,1,-1)
        b=contour_box(mask,(0,0),*size,.9);b.update(id=f'b{i}',order=i,panel_id='p1');bubbles.append(b)
        a=rectangle(text,*size,1,margin=0);anchors[b['id']]={k:a[k] for k in ('x','y','w','h')}
    return dict(result=dict(width=1000,height=500,direction='ltr',layout='auto',bubbles=bubbles,
        panels=[dict(id='p1',x=0,y=0,w=1,h=1)]),analysis=dict(reading_anchors=anchors,text_check=dict(regions=[dict(region_id='b1',ocr=[dict(text='Short reply')]),dict(region_id='b2',ocr=[dict(text='Long speech')])])),review=dict(verified=False,flags=['Check b2']))


def test_long_speech_and_short_reply_are_ordered_by_adjacent_bodies():
    d=document();old=copy.deepcopy(d);refine_body_order(Image.new('RGB',(1000,500)),d)
    assert d['result']['bubbles'][0]['x']<d['result']['bubbles'][1]['x']
    assert d['analysis']['reading_anchors']['b1']==old['analysis']['reading_anchors']['b2']
    assert d['analysis']['text_check']['regions'][0]['region_id']=='b2'
    assert d['review']['flags'][0]=='Check b1'
    assert d['analysis']['page_context']['original']==old


def test_nested_compound_extent_cannot_reorder_the_other_speakers():
    d=document();d['result']['bubbles'][0].update(x=.05,y=.02,w=.8,h=.8);old=copy.deepcopy(d)
    assert refine_body_order(Image.new('RGB',(1000,500)),d)==old


def test_text_paragraphs_and_verified_results_keep_their_order():
    for verified in (False,True):
        d=document();d['result']['bubbles'][0]['type']='text';d['review']['verified']=verified;old=copy.deepcopy(d)
        assert refine_body_order(Image.new('RGB',(1000,500)),d)==old
