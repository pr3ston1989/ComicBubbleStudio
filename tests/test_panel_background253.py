import copy
import cv2,numpy as np
import pytest
from PIL import Image
from tools.bubble_studio.geometry import contour_box,rectangle
from tools.bubble_studio.panel_background import proposal,refine


def scene(scale=1,mirror=False):
 size=round(400*scale);points=np.array([[20,20],[360,20],[360,80],[180,80],[180,380],[20,380]])*scale;mask=np.zeros((size,size),np.uint8);cv2.fillPoly(mask,[np.rint(points).astype(np.int32)],1)
 text=dict(box=[40*scale,150*scale,140*scale,210*scale],label=2,score=.95)
 if mirror:mask=cv2.flip(mask,1);text['box']=[size-text['box'][2],text['box'][1],size-text['box'][0],text['box'][3]]
 b=contour_box(mask,(0,0),size,size,.9);b.update(id='b1',order=1,panel_id='p1');anchor=rectangle(text['box'],size,size,1,margin=0)
 d=dict(result=dict(bubbles=[b],panels=[dict(id='p1',x=.05,y=.05,w=.9,h=.9)]),analysis=dict(reading_anchors=dict(b1={k:anchor[k] for k in ('x','y','w','h')}),balloons=[dict(supporting_texts=[text])],text_check=dict(regions=[dict(region_id='b1',box=[0,0,size,size],ocr=[dict(text='A FREE THOUGHT',score=.99,box=[v/size for v in text['box']])])])),review=dict(verified=False,flags=[]))
 return Image.new('RGB',(size,size),'white'),d


@pytest.mark.parametrize('scale',[1,1.5])
@pytest.mark.parametrize('mirror',[False,True])
def test_free_text_mask_following_three_panel_edges_is_bounded_to_all_words(scale,mirror):
 im,d=scene(scale,mirror);old=copy.deepcopy(d);refine(im,d);b=d['result']['bubbles'][0]
 assert b['type']=='text' and not b.get('polygons') and b['w']*b['h']<old['result']['bubbles'][0]['w']*old['result']['bubbles'][0]['h']*.25
 assert d['analysis']['reading_anchors']==old['analysis']['reading_anchors']
 assert [b[k] for k in ('id','order','panel_id')]==['b1',1,'p1']
 assert d['analysis']['panel_background_repair']['changes'][0]['original_region']==old['result']['bubbles'][0]


@pytest.mark.parametrize('kind',['real-balloon','weak-detector','unassigned-weak-word','two-panel-edges','verified','missing-ocr'])
def test_ambiguous_geometry_or_text_never_authorizes_a_crop(kind):
 im,d=scene()
 if kind=='real-balloon':d['analysis']['balloons'][0]['supporting_texts'][0]['label']=1
 elif kind=='weak-detector':d['analysis']['balloons'][0]['supporting_texts'][0]['score']=.89
 elif kind=='unassigned-weak-word':d['analysis']['text_check']['regions'][0]['ocr'].append(dict(text='maybe',score=.3,box=[.6,.1,.8,.18]))
 elif kind=='two-panel-edges':d['result']['panels'][0]['y']=.01
 elif kind=='verified':d['review']['verified']=True
 elif kind=='missing-ocr':d['analysis']['text_check']['regions'][0]['ocr']=[]
 old=copy.deepcopy(d);assert refine(im,d)==old


def test_uniform_compact_actual_body_is_not_a_panel_background():
 im,d=scene();mask=np.zeros((400,400),np.uint8);mask[20:381,20:361]=1;b=contour_box(mask,(0,0),400,400,.9);b.update(id='b1',order=1,panel_id='p1');d['result']['bubbles']=[b]
 assert proposal(im,d,b) is None
