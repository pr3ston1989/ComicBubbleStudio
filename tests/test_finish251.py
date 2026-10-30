import copy
import cv2,numpy as np
import pytest
from PIL import Image
from tools.bubble_studio.geometry import rectangle,contour_box
from tools.bubble_studio.panel_gutters import gutter_groups,refine_gutter_order
from tools.bubble_studio.editorial_audit import refine_editorial,refine_publishing_regions,publishing_markers
from tools.bubble_studio.exact_duplicates import remove_exact_duplicates
from tools.bubble_studio.native_body import recover_body,recover_page_bodies,audit_body
from tools.bubble_studio.page_context import restore_page_context
from tools.bubble_studio.finish251 import refine_page
from tools.bubble_studio.promotion_audit import promotion_evidence,refine_promotion

class Semantic:
 def __init__(self,answer):self.answer=answer;self.calls=0
 def _ask(self,*args):self.calls+=1;return self.answer
 def region_role(self,*args):self.calls+=1;return self.answer

def document(boxes,direction='ltr'):
 bubbles=[dict(rectangle(box,1000,1000,.9,'text',margin=0),id=f'b{i+1}',order=i+1,panel_id=None) for i,box in enumerate(boxes)]
 return dict(result=dict(width=1000,height=1000,layout='auto',direction=direction,bubbles=bubbles,panels=[],confidence=.9),analysis=dict(reading_anchors={b['id']:{k:b[k] for k in ('x','y','w','h')} for b in bubbles},page_context=dict(status='unchanged',classification=dict(kind='story',contains_readable_story=True)),text_check=dict(regions=[])),review=dict(verified=False,flags=[]))

@pytest.mark.parametrize('direction',['ltr','rtl'])
@pytest.mark.parametrize('paper',[0,255])
def test_physical_row_gutters_keep_entire_panels_together(direction,paper):
 rgb=np.full((1000,1000,3),paper,np.uint8)
 for x,y,xx,yy in [(30,30,970,460),(30,490,475,970),(510,490,970,970)]:cv2.rectangle(rgb,(x,y),(xx,yy),(110,145,170),-1)
 d=document([[100,100,200,150],[150,550,250,610],[700,550,800,610],[150,750,250,810],[700,750,800,810]],direction)
 im=Image.fromarray(rgb);groups=gutter_groups(im,d);assert len(groups)==3
 expected=['b1','b2','b4','b3','b5'] if direction=='ltr' else ['b1','b3','b5','b2','b4']
 assert [i for g in groups for i in g['regions']]==expected
 before=copy.deepcopy(d);semantic=Semantic(dict(all_physical_panel_gutters=True));refine_gutter_order(im,d,semantic)
 assert [d['analysis']['reading_anchors'][b['id']] for b in d['result']['bubbles']]==[before['analysis']['reading_anchors'][i] for i in expected]
 assert d['analysis']['gutter_order']['original']==before

def test_text_crossing_a_gutter_uncertain_vision_and_4koma_keep_original_order():
 rgb=np.full((1000,1000,3),255,np.uint8);cv2.rectangle(rgb,(30,30),(970,470),(120,120,120),-1);cv2.rectangle(rgb,(30,510),(970,970),(120,120,120),-1);im=Image.fromarray(rgb)
 d=document([[100,100,200,150],[100,800,200,850],[700,200,800,250]])
 before=copy.deepcopy(d);assert refine_gutter_order(im,d,Semantic(dict(all_physical_panel_gutters=False)))==before
 d['analysis']['strip_reading']=dict(columns=[['p1','p2','p3','p4']]);assert gutter_groups(im,d)==[]
 d['analysis'].pop('strip_reading');d['analysis']['reading_anchors']['b1'].update(y=.45,h=.1);assert gutter_groups(im,d)==[]

def test_exact_duplicate_removal_never_discards_different_words_or_contours():
 d=document([[100,100,200,200],[100,100,200,200],[100,100,200,200]])
 d['analysis']['reading_anchors']['b3']['y']+=.001
 before=copy.deepcopy(d);remove_exact_duplicates(d)
 assert len(d['result']['bubbles'])==2 and d['analysis']['exact_duplicate_removal']['removed']==['b2']
 assert d['analysis']['exact_duplicate_removal']['original']==before

@pytest.mark.parametrize('answer',[dict(category='story_or_mixed',contains_story_text=True),dict(category='uncertain',contains_story_text=False),dict(category='single_cover',contains_story_text='false'),{}])
def test_editorial_requires_two_actual_no_story_decisions(answer):
 d=document([[100,100,200,200]]);d['analysis']['page_context']['classification']=dict(kind='illustration',contains_readable_story=False);before=copy.deepcopy(d)
 assert refine_editorial(Image.new('RGB',(1000,1000)),d,Semantic(answer))==before

def test_real_credits_can_be_removed_while_story_titles_and_dialogue_survive():
 d=document([[100,100,200,200],[400,100,700,200]])
 d['analysis']['page_context']['classification']=dict(kind='credits',contains_readable_story=False)
 d['analysis']['text_check']['regions']=[dict(region_id='b1',ocr=[dict(text='Writer Artist Letterer',score=.99)]),dict(region_id='b2',ocr=[dict(text='PART THREE',score=.99)])]
 before=copy.deepcopy(d);refine_publishing_regions(Image.new('RGB',(1000,1000)),d,Semantic(dict(role='editorial',enclosure='none')))
 assert len(d['result']['bubbles'])==1 and d['analysis']['text_check']['regions'][0]['ocr'][0]['text']=='PART THREE'
 assert publishing_markers([dict(text='Writer Artist',score=.3)])==[]
 for enclosure in ['balloon','caption','uncertain']:
  d=copy.deepcopy(before);assert refine_publishing_regions(Image.new('RGB',(1000,1000)),d,Semantic(dict(role='editorial',enclosure=enclosure)))==before

def native_scene(scale=1,mirror=False):
 rgb=np.full((700,700,3),70,np.uint8);cv2.ellipse(rgb,(350,180),(100,75),0,0,360,(255,255,255),-1)
 cv2.fillPoly(rgb,[np.array([[330,235],[355,235],[380,620]],np.int32)],(255,255,255));cv2.putText(rgb,'HELLO',(306,190),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,0,0),2)
 mask=np.zeros((700,700),np.uint8);cv2.ellipse(mask,(350,180),(100,75),0,0,360,1,-1)
 text=dict(box=[305,174,365,194],label=1,score=.99)
 if mirror:rgb=cv2.flip(rgb,1);mask=cv2.flip(mask,1);text['box']=[700-text['box'][2],text['box'][1],700-text['box'][0],text['box'][3]]
 size=round(700*scale);rgb=cv2.resize(rgb,(size,size),interpolation=cv2.INTER_NEAREST);mask=cv2.resize(mask,(size,size),interpolation=cv2.INTER_NEAREST);text['box']=[v*scale for v in text['box']]
 bubble=contour_box(mask,(0,0),size,size,.95);bubble.update(id='b1',order=1,panel_id='p1');a=rectangle(text['box'],size,size,1,margin=0)
 d=dict(result=dict(bubbles=[bubble],panels=[dict(id='p1',x=.1,y=.1,w=.8,h=.85)]),analysis=dict(reading_anchors=dict(b1={k:a[k] for k in ('x','y','w','h')}),balloons=[dict(supporting_texts=[text])],text_check=dict(regions=[dict(region_id='b1',box=[0,0,size,size],ocr=[dict(text='HELLO',score=.99,box=[v/size for v in text['box']])])])),review=dict(verified=False,flags=[]))
 return Image.fromarray(rgb),d,bubble

@pytest.mark.parametrize('scale',[1,1.5])
@pytest.mark.parametrize('mirror',[False,True])
def test_long_native_tail_can_extend_beyond_old_crop_without_changing_words(scale,mirror):
 image,d,b=native_scene(scale,mirror);r,a=recover_body(image,d,b)
 assert a and r['y']+r['h']>.87
 assert (r['id'],r['order'],r['panel_id'])==(b['id'],b['order'],b['panel_id'])

def test_native_body_never_consumes_a_neighbour_or_uses_missing_ocr():
 im,d,b=native_scene();d['analysis']['text_check']['regions']=[];assert recover_body(im,d,b)==(b,None)
 im,d,b=native_scene();other=dict(rectangle([365,500,385,550],700,700,.99,'text',margin=0),id='b2');d['result']['bubbles'].append(other);d['analysis']['reading_anchors']['b2']={k:other[k] for k in ('x','y','w','h')};assert recover_body(im,d,b)==(b,None)

def test_verified_pages_bypass_all_new_stages():
 d=document([[100,100,200,200],[100,100,200,200]]);d['review']['verified']=True;before=copy.deepcopy(d);semantic=Semantic(None)
 assert refine_page(Image.new('RGB',(1000,1000)),d,None,semantic)==before and semantic.calls==0

def promotion_doc():
 d=document([[100,100,200,200]])
 d['analysis']['page_context']['classification']=dict(kind='mixed',contains_readable_story=True)
 d['analysis']['text_check']['regions']=[dict(region_id='b1',ocr=[dict(text='NEXT ISSUE / COLLECTED EDITION / All rights reserved',score=.99)])]
 return d

@pytest.mark.parametrize('answer',[{},dict(entire_page_is_real_world_promotion=False),dict(entire_page_is_real_world_promotion='true')])
def test_promotion_keeps_story_unless_the_visual_answer_is_an_actual_true(answer):
 d=promotion_doc();before=copy.deepcopy(d);assert refine_promotion(Image.new('RGB',(1000,1000)),d,Semantic(answer))==before

def test_promotion_requires_two_separate_confirmations_and_reversible_evidence():
 class TwoAnswers:
  def __init__(self,last):self.last=last;self.calls=0
  def _ask(self,*args):
   self.calls+=1;return dict(entire_page_is_real_world_promotion=True) if self.calls==1 else dict(advertising_layout_without_story=self.last)
 for last in [True,False]:
  d=promotion_doc();before=copy.deepcopy(d);s=TwoAnswers(last);refine_promotion(Image.new('RGB',(1000,1000)),d,s)
  assert s.calls==2
  if last:assert not d['result']['bubbles'] and d['analysis']['promotion_audit']['original']==before
  else:assert d==before

def test_marketing_terms_in_story_and_fictional_biography_do_not_authorize_a_page_omission():
 d=promotion_doc();d['analysis']['page_context']['classification']['kind']='story';assert promotion_evidence(d) is None
 d=promotion_doc();d['analysis']['text_check']['regions'][0]['ocr'].append(dict(text='PART THREE',score=.99));assert promotion_evidence(d) is None

def test_context_failure_keeps_detections_and_parks_the_model():
 class Offline:
  def __init__(self):self.parked=False
  def _ask(self,*args):raise RuntimeError('offline')
  def park(self):self.parked=True
 d=promotion_doc();before=copy.deepcopy(d['result']);s=Offline();refine_page(Image.new('RGB',(1000,1000)),d,None,s)
 assert d['result']==before and s.parked and d['analysis']['refinement251_error']=='RuntimeError'

@pytest.mark.parametrize('answer',[{},dict(body_outline_correct=True,contains_unrelated_art=True,text_truncated=False),dict(body_outline_correct=True,contains_unrelated_art=False,text_truncated=True),dict(body_outline_correct='true',contains_unrelated_art=False,text_truncated=False)])
def test_rectangle_body_requires_complete_visual_confirmation(answer):
 im,d,b=native_scene();assert audit_body(im,b,Semantic(answer)) is None

def test_actual_body_audit_uses_original_and_marked_crop():
 class Audit:
  def _ask(self,images,prompt,max_tokens):
   assert len(images)==2 and images[0].size==images[1].size and images[0].tobytes()!=images[1].tobytes()
   return dict(body_outline_correct=True,contains_unrelated_art=False,text_truncated=False)
 im,d,b=native_scene();assert audit_body(im,b,Audit())['body_outline_correct']

@pytest.mark.parametrize('strict',[False,True])
def test_unavailable_outline_audit_cannot_authorize_a_rectangle_replacement(strict):
 class Unavailable:
  def _ask(self,*args):raise RuntimeError('unavailable')
 s=Unavailable();s.strict=strict;im,d,b=native_scene()
 if strict:
  with pytest.raises(RuntimeError):audit_body(im,b,s)
 else:assert audit_body(im,b,s) is None
