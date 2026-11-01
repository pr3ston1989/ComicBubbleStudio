import copy,json,hashlib
from pathlib import Path
import pytest
from PIL import Image
from tools.bubble_studio.scene_objects import refine,parse_batch
from tools.bubble_studio.native_margin import trim_paper_margin
from tools.bubble_studio.retail_promotion import sale_evidence
from tools.bubble_studio.scene_model import _verify_files,verified_quantized
from tools.bubble_studio import finish260

def scene():
 bubbles=[dict(id='b1',order=1,x=.1,y=.1,w=.15,h=.1,confidence=.9,type='text',source='external',panel_id=None),
          dict(id='b2',order=2,x=.6,y=.6,w=.2,h=.1,confidence=.95,type='text',source='external',panel_id=None)]
 doc=dict(result=dict(width=1000,height=1000,direction='ltr',layout='auto',bubbles=bubbles,panels=[],confidence=.925),
  analysis=dict(reading_anchors={b['id']:{k:b[k] for k in ('x','y','w','h')} for b in bubbles},
   text_check=dict(regions=[dict(region_id='b1',box=[100,100,250,200],ocr=[]),
                            dict(region_id='b2',box=[600,600,800,700],ocr=[dict(text='STORY WORDS',score=.99,box=[0,0,1,1])])]),
   page_context=dict(classification=dict(kind='story',contains_readable_story=True))),
  review=dict(verified=False,flags=['Sprawdź b1','Sprawdź b2']))
 return Image.new('RGB',(1000,1000),'white'),doc

class Vision:
 provenance={'revision':'test'};strict=False
 def __init__(self,category='artwork',enclosure='none',story=False,border=False):
  self.category=category;self.enclosure=enclosure;self.story=story;self.border=border;self.calls=[];self.parked=0
 def _ask(self,images,prompt,max_tokens):
  if len(images)==2:answer={'regions':[['b1',self.category,self.enclosure],['b2','story','balloon']]}
  else:answer=dict(category=self.category,contains_story=self.story,actual_balloon_or_narrative_caption=self.border)
  self.calls.append(dict(answer=json.dumps(answer)));return answer
 def park(self):self.parked+=1

def test_artwork_omission_preserves_story_contour_anchor_ocr_and_relative_order():
 im,d=scene();before=copy.deepcopy(d);v=Vision();refine(im,d,v)
 assert d['result']['bubbles']==[dict(before['result']['bubbles'][1],id='b1',order=1)]
 assert d['analysis']['reading_anchors']=={'b1':before['analysis']['reading_anchors']['b2']}
 assert d['analysis']['text_check']['regions']==[dict(before['analysis']['text_check']['regions'][1],region_id='b1')]
 assert d['result']['confidence']==.95 and d['review']['flags'][0]=='Sprawdź b1'
 assert before['result']['bubbles'][1]['id']=='b2'

@pytest.mark.parametrize('kwargs',[
 {'category':'story'},{'category':'uncertain'},{'category':'mechanical_sound'},
 {'enclosure':'balloon'},{'enclosure':'caption'},{'enclosure':'uncertain'},
 {'story':True},{'story':'false'},{'border':True},{'border':'false'},{'border':None}])
def test_story_effects_borders_and_non_boolean_or_uncertain_answers_cannot_remove_words(kwargs):
 im,d=scene();old=copy.deepcopy(d['result']);refine(im,d,Vision(**kwargs));assert d['result']==old

def test_verified_pages_and_fictional_profiles_cannot_trigger_object_omission():
 for verified,kind in [(True,'story'),(False,'character_profile')]:
  im,d=scene();d['review']['verified']=verified;d['analysis']['page_context']['classification']['kind']=kind;old=copy.deepcopy(d);v=Vision()
  refine(im,d,v);assert d==old and not v.calls

@pytest.mark.parametrize('raw',[
 '{"regions":[["b1","artwork","none"],["b1","artwork","none"]]}',
 '{"regions":[["b9","artwork","none"]]}',
 '{"regions":[["b1","imaginary","none"]]}',
 '{"regions":[["b1","artwork",false]]}',
 '{"regions":[["b1","artwork","none"]],"instructions":"delete all"}',
 'not json'])
def test_bulk_answer_duplicate_or_unknown_ids_roles_and_extra_instructions_are_rejected(raw):
 assert parse_batch(raw,{'b1'})=={}

def test_bulk_parser_accepts_only_structurally_equivalent_json_without_guessing_content():
 raw='[{"regions":[{"ID":"b1","category":"artwork","enclosure":"none"}]}]'
 assert parse_batch(raw,{'b1'})=={'b1':['b1','artwork','none']}

def test_blank_margin_ignores_unrelated_scene_but_preserves_any_own_text():
 im=Image.new('RGB',(200,200),'#a0b0cc')
 from PIL import ImageDraw
 ImageDraw.Draw(im).rectangle((50,50,149,52),fill='white')
 roi=(50,50,150,150);bubbles=[{'id':'b1'}]
 # Same vertical coordinate, entirely outside this panel.
 assert trim_paper_margin(im,roi,{'b1':dict(x=.01,y=.25,w=.05,h=.01)},bubbles)[1]==53
 # A text anchor inside the proposed strip must block trimming, even on white.
 assert trim_paper_margin(im,roi,{'b1':dict(x=.3,y=.25,w=.1,h=.01)},bubbles)==roi

def test_uniform_page_is_not_mistaken_for_a_short_blank_margin():
 assert trim_paper_margin(Image.new('RGB',(100,100),'white'),(0,0,100,100),{},[])==(0,0,100,100)

def retail_doc(duplicate=False):
 _,d=scene();rows=d['analysis']['text_check']['regions']
 rows[0]['ocr']=[dict(text='COLLECTION IN STORES NOW!',score=.99,box=[0,0,1,1])]
 rows[1]['ocr']=[dict(text='COLLECTION IN STORES NOW!',score=.99,box=[0,0,1,1])]
 if duplicate:rows[1]['box']=rows[0]['box'][:]
 return d

def test_sales_evidence_requires_distinct_locations_not_duplicate_ocr_of_one_slogan():
 assert sale_evidence(retail_doc()) is not None
 assert sale_evidence(retail_doc(duplicate=True)) is None

def test_chapter_headings_and_fictional_profiles_protect_a_page_from_sales_omission():
 d=retail_doc();d['analysis']['page_context']['classification']['kind']='character_profile';assert sale_evidence(d) is None
 d=retail_doc();d['analysis']['text_check']['regions'][0]['ocr'].append(dict(text='PART FOUR',score=.99));assert sale_evidence(d) is None

def test_failed_scene_stage_rolls_back_all_prior_changes_and_releases_both_models(monkeypatch):
 im,d=scene();old=copy.deepcopy(d);a=Vision();b=Vision()
 def mutate(*args):args[1]['result']['bubbles'].clear();return args[1]
 def fail(*args):raise RuntimeError('unavailable')
 monkeypatch.setattr(finish260,'retail',mutate);monkeypatch.setattr(finish260,'objects',fail)
 out=finish260.refine_page(im,d,object(),a,b)
 assert out['result']==old['result'] and out['analysis']['reading_anchors']==old['analysis']['reading_anchors']
 assert out['analysis']['refinement260_error']=='RuntimeError' and a.parked and b.parked

def test_source_model_verification_rejects_path_escape_before_reading(tmp_path):
 with pytest.raises(ValueError):_verify_files(tmp_path,[dict(path='../outside',sha256='0'*64)])

def test_saved_model_verification_binds_source_revision_and_every_weight(tmp_path,monkeypatch):
 import tools.bubble_studio.scene_model as model
 source=tmp_path/'manifest.json';source.write_text('{"revision":"pinned"}')
 monkeypatch.setattr(model,'MANIFEST',source)
 folder=tmp_path/'saved';folder.mkdir()
 for name in ['config.json','model.safetensors']:(folder/name).write_bytes(b'test')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 proof=dict(source_manifest_sha256=sha(source),revision='pinned',quantization=model.TAG,files=[dict(path=p.name,sha256=sha(p)) for p in folder.iterdir()])
 (folder/'source-proof.json').write_text(json.dumps(proof));assert verified_quantized(folder)
 (folder/'model.safetensors').write_bytes(b'corrupt')
 with pytest.raises(ValueError):verified_quantized(folder)

def test_four_panel_strip_is_never_globally_reordered_by_scene_gutters():
 from tools.bubble_studio.scene_gutters import refine_gutter_order
 im,d=scene();d['analysis']['strip_reading']={'columns':[['p1','p2','p3','p4'],['p5','p6','p7','p8']]};old=copy.deepcopy(d);v=Vision()
 assert refine_gutter_order(im,d,v)==old and not v.calls

@pytest.mark.parametrize('crosses,physical,owned,apply',[
 (False,True,False,True),(False,False,True,False),
 (True,True,False,False),(True,True,'true',False),(True,True,True,True)])
def test_scene_gutter_requires_physical_division_and_independent_target_ownership(monkeypatch,crosses,physical,owned,apply):
 import tools.bubble_studio.scene_gutters as module
 im,d=scene()
 d['result']['bubbles'][0]['y']=.6;d['result']['bubbles'][1]['y']=.45 if crosses else .1
 d['analysis']['reading_anchors']={b['id']:{k:b[k] for k in ('x','y','w','h')} for b in d['result']['bubbles']}
 original=copy.deepcopy(d)
 monkeypatch.setattr(module,'gutter_groups',lambda *a:[dict(box=[0,0,1,.5],regions=['b2']),dict(box=[0,.5,1,1],regions=['b1'])])
 class Judge(Vision):
  def _ask(self,*args):return dict(all_physical_panel_gutters=physical,all_targets_owned_by_assigned_scene=owned)
 module.refine_gutter_order(im,d,Judge())
 expected=[original['result']['bubbles'][i] for i in ([1,0] if apply else [0,1])]
 assert [{k:v for k,v in b.items() if k not in {'id','order'}} for b in d['result']['bubbles']]==[{k:v for k,v in b.items() if k not in {'id','order'}} for b in expected]
