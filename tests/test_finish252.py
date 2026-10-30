import copy
import pytest
from PIL import Image
from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.nonstory_mask import refine
from tools.bubble_studio.finish252 import refine_page
from tools.bubble_studio.page_context import restore_page_context


def scene(text='MAITLAND LIVES'):
 bubbles=[dict(rectangle([100,100,250,150],1000,1000,.9,'text',margin=0),id='b1',order=1,panel_id=None),dict(rectangle([600,100,800,200],1000,1000,.95,'text',margin=0),id='b2',order=2,panel_id=None)]
 d=dict(result=dict(width=1000,height=1000,bubbles=bubbles,confidence=.925,direction='ltr',layout='auto',panels=[]),analysis=dict(reading_anchors={b['id']:{k:b[k] for k in ('x','y','w','h')} for b in bubbles},text_check=dict(regions=[dict(region_id='b1',ocr=[dict(text=text,score=.99)])]),page_context=dict(status='unchanged',classification=dict(kind='story',contains_readable_story=True))),review=dict(verified=False,flags=['Sprawdź b1','Sprawdź b2']))
 return Image.new('RGB',(1000,1000),'white'),d


class Vision:
 strict=False
 def __init__(self,role='physical_sign',enclosure='none',category='physical_sign',border=False):
  self.role=role;self.enclosure=enclosure;self.category=category;self.border=border;self.calls=0;self.parked=False
 def region_role(self,*args):self.calls+=1;return dict(role=self.role,enclosure=self.enclosure)
 def _ask(self,images,*args):
  assert len(images)==3 and images[1].tobytes()!=images[2].tobytes()
  self.calls+=1;return dict(category=self.category,has_real_balloon_or_caption=self.border)
 def park(self):self.parked=True


def test_confirmed_incidental_sign_removed_without_changing_story_geometry_or_anchors():
 im,d=scene();old=copy.deepcopy(d);s=Vision();refine_page(im,d,s)
 assert len(d['result']['bubbles'])==1 and s.calls==2 and s.parked
 kept=dict(old['result']['bubbles'][1],id='b1',order=1)
 assert d['result']['bubbles']==[kept]
 assert d['analysis']['reading_anchors']==dict(b1=old['analysis']['reading_anchors']['b2'])
 assert d['review']['flags'][0]=='Sprawdź b1'
 assert d['analysis']['page_context']['status']=='applied'
 assert restore_page_context(d) is True
 assert d['result']==old['result'] and d['analysis']['reading_anchors']==old['analysis']['reading_anchors']
 assert d['review']==old['review'] and d['analysis']['page_context']['status']=='restored'


@pytest.mark.parametrize('role,enclosure,category,border',[
 ('dialogue','none','physical_sign',False),('thought','none','physical_sign',False),
 ('narration','none','physical_sign',False),('fictional_profile','none','physical_sign',False),
 ('physical_sign','balloon','physical_sign',False),('physical_sign','caption','physical_sign',False),
 ('physical_sign','uncertain','physical_sign',False),('physical_sign','none','editorial',False),
 ('physical_sign','none','uncertain',False),('physical_sign','none','physical_sign',True),
 ('physical_sign','none','physical_sign','false'),('physical_sign','none','physical_sign',None)])
def test_story_real_borders_disagreement_and_uncertainty_cannot_authorize_omission(role,enclosure,category,border):
 im,d=scene();before=copy.deepcopy(d)
 assert refine_page(im,d,Vision(role,enclosure,category,border))==before


@pytest.mark.parametrize('text',['MELT','PARAMED','Dragon?'])
def test_single_word_sign_classification_does_not_delete_symbolic_or_spoken_words(text):
 im,d=scene(text);before=copy.deepcopy(d);s=Vision();assert refine_page(im,d,s)==before and s.calls==1


def test_fictional_profile_fields_and_human_verified_pages_are_preserved_without_visual_calls():
 for kind in ['profile','verified']:
  im,d=scene('COMPANY NAME')
  if kind=='profile':d['analysis']['page_context']['classification']['kind']='character_profile'
  else:d['review']['verified']=True
  before=copy.deepcopy(d);s=Vision();assert refine_page(im,d,s)==before and s.calls==0


@pytest.mark.parametrize('score',[.84,.2])
def test_weak_ocr_does_not_trigger_a_destructive_decision(score):
 im,d=scene();d['analysis']['text_check']['regions'][0]['ocr'][0]['score']=score;before=copy.deepcopy(d);s=Vision()
 assert refine_page(im,d,s)==before and s.calls==0


@pytest.mark.parametrize('role',['mechanical_sound','editorial'])
def test_confirmed_free_effect_or_credit_can_be_removed(role):
 im,d=scene('BANG!' if role=='mechanical_sound' else 'Artist Name');refine_page(im,d,Vision(role,category=role))
 assert len(d['result']['bubbles'])==1


@pytest.mark.parametrize('strict',[False,True])
def test_unavailable_visual_check_rolls_back_the_whole_stage_and_releases_memory(strict):
 class Broken(Vision):
  def _ask(self,*args):raise RuntimeError('unavailable')
 im,d=scene();before=copy.deepcopy(d);s=Broken();s.strict=strict
 if strict:
  with pytest.raises(RuntimeError):refine_page(im,d,s)
 else:
  actual=refine_page(im,d,s);assert actual['result']==before['result'] and actual['analysis']['reading_anchors']==before['analysis']['reading_anchors']
 assert s.parked
