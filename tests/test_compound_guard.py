import copy
import cv2
import numpy as np
from PIL import Image
from tools.bubble_studio.geometry import contour_box,rectangle
from tools.bubble_studio.compound_guard import recover_compounds
from tools.bubble_studio.quality_guard import _polygons
from tools.bubble_studio.page_context import restore_page_context
from tools.bubble_studio.thin_bridges import skeleton


def scene(joined=True,blank=False,neighbour=False):
    width,height=900,500;shape=np.zeros((height,width),np.uint8);parts=[]
    for x in (230,650):
        mask=np.zeros_like(shape);cv2.ellipse(mask,(x,240),(120,100),0,0,360,1,-1);parts.append(mask);shape|=mask
    if joined:cv2.rectangle(shape,(330,233),(550,247),1,-1)
    rgb=np.full((height,width,3),(90,130,170),np.uint8);rgb[shape>0]=0
    inside=cv2.erode(shape,np.ones((5,5),np.uint8));rgb[inside>0]=255
    bubbles=[];anchors={};diagnostics=[]
    for n,(mask,x) in enumerate(zip(parts,(230,650)),1):
        b=contour_box(mask,(0,0),width,height,.95);b.update(id=f'b{n}',order=n,panel_id='p1');bubbles.append(b)
        box=[x-60,215,x+60,260];a=rectangle(box,width,height,1,margin=0);anchors[b['id']]={k:a[k] for k in ('x','y','w','h')}
        diagnostics.append(dict(supporting_texts=[dict(label=1,score=.96,box=box)]))
        for xx in range(x-50,x+45,20):cv2.rectangle(rgb,(xx,225),(xx+7,245),(0,0,0),-1)
    if blank:rgb[:]=255
    if neighbour:
        b=dict(rectangle([430,235,455,245],width,height,.95,'text',margin=0),id='b3',order=3,panel_id='p1');bubbles.append(b);anchors['b3']={k:b[k] for k in ('x','y','w','h')}
    doc=dict(result=dict(width=width,height=height,direction='ltr',layout='auto',confidence=.95,
        panels=[dict(id='p1',x=0,y=0,w=1,h=1)],bubbles=bubbles),analysis=dict(reading_anchors=anchors,balloons=diagnostics),review=dict(verified=False,flags=[]))
    return Image.fromarray(rgb),doc


class Checker:
    def review(self,image,doc):doc['analysis']['text_check']=dict(mode='review',regions=[dict(region_id=b['id'],ocr=[]) for b in doc['result']['bubbles']])


def test_actual_paper_connector_merges_the_lobes_without_losing_old_pixels():
    image,doc=scene();old=copy.deepcopy(doc)
    recover_compounds(image,doc,Checker())
    assert len(doc['result']['bubbles'])==1
    merged=doc['result']['bubbles'][0];assert merged['id']=='b1' and merged['order']==1
    mask=np.zeros((image.height,image.width),np.uint8);cv2.fillPoly(mask,_polygons(merged,*image.size),1)
    for b in old['result']['bubbles']:
        original=np.zeros_like(mask);cv2.fillPoly(original,_polygons(b,*image.size),1)
        assert np.sum(mask&original)/np.sum(original)>=.999
    assert set(doc['analysis']['reading_anchors'])=={'b1'}
    assert restore_page_context(doc) and doc['result']==old['result']


def test_separate_balloons_do_not_merge_by_distance():
    image,doc=scene(joined=False);old=copy.deepcopy(doc)
    assert recover_compounds(image,doc,Checker())==old


def test_fallback_rectangle_corners_do_not_deform_the_recovered_balloon():
    image,doc=scene();doc['result']['bubbles'][1]=dict(rectangle([540,140,770,340],*image.size,.95,'text',margin=0),id='b2',order=2,panel_id='p1')
    recover_compounds(image,doc,Checker());assert len(doc['result']['bubbles'])==1
    merged=doc['result']['bubbles'][0];mask=np.zeros((image.height,image.width),np.uint8);cv2.fillPoly(mask,_polygons(merged,*image.size),1)
    assert not mask[145,545] and mask[240,650]


def test_another_reading_anchor_blocks_a_connector():
    image,doc=scene(neighbour=True);old=copy.deepcopy(doc)
    assert recover_compounds(image,doc,Checker())==old


def test_blank_image_has_no_connector_evidence_and_terminates():
    assert not np.any(skeleton(np.ones((50,50),np.uint8)))
    image,doc=scene(blank=True);old=copy.deepcopy(doc)
    assert recover_compounds(image,doc,Checker())==old


def test_human_verified_regions_are_immutable():
    image,doc=scene();doc['review']['verified']=True;old=copy.deepcopy(doc)
    assert recover_compounds(image,doc,Checker())==old
