"""Scale, reflection and rejection controls for continuation of a real tail."""
import copy
import cv2
import numpy as np
import pytest
from PIL import Image
from test_stroke_guard import scene
from tools.bubble_studio.geometry import contour_box,rectangle
from tools.bubble_studio.quality_guard import _polygons
from tools.bubble_studio.tail_continuation import recover_tail_continuation,continue_page_tails


def clipped(dark=False,scale=1,mirrored=False):
    image,region,texts=scene(complete=True,dark=dark,scale=scale)
    mask=np.zeros((image.height,image.width),np.uint8)
    cv2.fillPoly(mask,_polygons(region,*image.size,(0,0)),1)
    mask[:,:round(95*scale)]=0
    if mirrored:
        image=Image.fromarray(cv2.flip(np.asarray(image),1));mask=cv2.flip(mask,1)
    region=contour_box(mask,(0,0),*image.size,.94)
    region.update(id='b4',order=4,panel_id='p2')
    return image,region,texts


@pytest.mark.parametrize('dark',[False,True])
@pytest.mark.parametrize('scale',[1,1.5,2])
@pytest.mark.parametrize('mirrored',[False,True])
def test_only_the_native_tapered_continuation_is_added(dark,scale,mirrored):
    image,region,texts=clipped(dark,scale,mirrored);before=copy.deepcopy(region)
    result,audit=recover_tail_continuation(image,region,texts)
    assert audit and audit['mask_preserved']>=.999
    assert audit['branch_stability']>=.8 and len(result['polygons'])==1
    assert all(result[k]==region[k] for k in ('id','order','panel_id','confidence'))
    assert region==before


@pytest.mark.parametrize('dark',[False,True])
def test_complete_balloon_is_not_extended(dark):
    image,region,texts=scene(complete=True,dark=dark)
    result,audit=recover_tail_continuation(image,region,texts)
    assert result is region and audit is None


@pytest.mark.parametrize('texts',[[],[dict(label=2,score=.99)],[dict(label=1,score=.69)]])
def test_unconfirmed_or_free_text_does_not_authorize_tracing(texts):
    image,region,_=clipped()
    result,audit=recover_tail_continuation(image,region,texts)
    assert result is region and audit is None


def test_a_continuation_escaping_into_connected_art_is_rejected():
    image,region,texts=clipped();rgb=np.asarray(image).copy()
    cv2.line(rgb,(80,240),(0,299),(0,0,0),4)
    result,audit=recover_tail_continuation(Image.fromarray(rgb),region,texts)
    assert result is region and audit is None


def test_neighbouring_text_and_human_verification_are_protected():
    image,region,texts=clipped();anchor=rectangle(texts[0]['box'],*image.size,1,margin=0)
    other=dict(rectangle([79,234,90,242],*image.size,.9,'text',margin=0),id='b5',order=5,panel_id='p2')
    doc=dict(result=dict(bubbles=[region,other]),analysis=dict(reading_anchors={
        'b4':{k:anchor[k] for k in ('x','y','w','h')},'b5':{k:other[k] for k in ('x','y','w','h')}},
        balloons=[dict(supporting_texts=texts)]),review=dict(verified=False,flags=[]))
    before=copy.deepcopy(doc);assert continue_page_tails(image,doc)==before
    doc['review']['verified']=True;before=copy.deepcopy(doc)
    assert continue_page_tails(image,doc)==before
