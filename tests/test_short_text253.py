import copy
import pytest
from PIL import Image
from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.short_text import candidates,refine,separated_gap
from tools.bubble_studio.finish253 import refine_page
from tools.bubble_studio.page_context import restore_page_context


def scene():
 b=dict(rectangle([600,400,800,460],1000,1000,.95,'text',margin=0),id='b1',order=1,panel_id='p1')
 d=dict(result=dict(width=1000,height=1000,direction='ltr',layout='auto',bubbles=[b],panels=[],confidence=.95),analysis=dict(page_context=dict(status='unchanged',classification=dict(kind='story',contains_readable_story=True)),reading_anchors=dict(b1={k:b[k] for k in ('x','y','w','h')}),text_check=dict(regions=[dict(region_id='b1',ocr=[dict(text='ORIGINAL',score=.99)])])),review=dict(verified=False,flags=['Sprawdź b1']))
 row=dict(text='CITY NAME',score=.99,box=[100,100,300,140]);return Image.new('RGB',(1000,1000),'white'),d,[row]


class Reader:
 def __init__(self,rows):self.rows=rows
 def locate_context(self,*args):return self.rows
 def read(self,*args):return [dict(text='CITY NAME',score=.99,box=[.25,.32,.75,.68])]


class Vision:
 def __init__(self,border=False,story=True,complete=True,first='START',second='START'):
  self.border=border;self.story=story;self.complete=complete;self.first=first;self.second=second;self.calls=0
 def _ask(self,images,prompt,*args):
  self.calls+=1
  assert 'existing_reading_order' in prompt and 'target_xywh' in prompt
  if len(images)==2:return dict(category='narration',has_drawn_border_around_words=self.border,complete_single_utterance=self.complete,insert_after=self.first)
  assert len(images)==3;return dict(unframed_story_utterance=self.story,all_words_in_target=self.complete,insert_after=self.second)


def test_recovered_short_caption_preserves_every_old_geometry_anchor_ocr_and_relative_position():
 im,d,rows=scene();old=copy.deepcopy(d);refine(im,d,Reader(rows),Vision(),rows)
 assert len(d['result']['bubbles'])==2
 assert d['result']['bubbles'][1]==dict(old['result']['bubbles'][0],id='b2',order=2)
 assert d['analysis']['reading_anchors']['b2']==old['analysis']['reading_anchors']['b1']
 assert d['analysis']['text_check']['regions']==[dict(old['analysis']['text_check']['regions'][0],region_id='b2')]
 assert d['review']['flags'][0]=='Sprawdź b2'
 assert d['analysis']['short_text_recovery']['preserved_regions']==dict(b1='b2')


@pytest.mark.parametrize('kwargs',[dict(border=True),dict(border='false'),dict(border=None),dict(story=False),dict(story='true'),dict(complete=False),dict(complete='true'),dict(first='b1',second='START'),dict(first='START|b1',second='START|b1')])
def test_real_borders_partial_words_uncertainty_or_disagreement_do_not_add_text(kwargs):
 im,d,rows=scene();before=copy.deepcopy(d);assert refine(im,d,Reader(rows),Vision(**kwargs),rows)==before


def test_time_caption_below_first_stop_cannot_be_inserted_at_start_by_two_wrong_answers():
 im,d,rows=scene();rows[0]['box']=[100,700,300,740];refine(im,d,Reader(rows),Vision(),rows)
 assert d['result']['bubbles'][1]['type']=='text' and d['result']['bubbles'][1]['y']>.6
 assert d['analysis']['short_text_recovery']['additions'][0]['insert_after']=='b1'
 assert d['analysis']['short_text_recovery']['additions'][0]['order_evidence']=='complete-prefix/suffix-vertical-separation'


def test_full_width_separator_never_interleaves_independent_strips():
 im,d,rows=scene();anchors=[dict(x=.8,y=y,w=.1,h=.05) for y in [.05,.3,.6,.8]]+[dict(x=.1,y=y,w=.1,h=.05) for y in [.05,.3,.6,.8]]
 d['result']['bubbles']=[dict(a,id=f'b{i+1}') for i,a in enumerate(anchors)];d['analysis']['reading_anchors']={b['id']:a for b,a in zip(d['result']['bubbles'],anchors)}
 d['analysis']['strip_reading']=dict(columns=[['p1','p2','p3','p4'],['p5','p6','p7','p8']])
 assert separated_gap(d,dict(x=.1,y=.02,w=.1,h=.02)) is None


def test_two_agreeing_model_answers_cannot_insert_a_label_beside_an_existing_utterance():
 im,d,rows=scene();rows[0]['box']=[100,400,300,440];before=copy.deepcopy(d);v=Vision()
 assert refine(im,d,Reader(rows),v,rows)==before and v.calls==0


def test_native_reading_disagreement_blocks_clipped_or_wrong_words():
 class Different(Reader):
  def read(self,*args):return [dict(text='OTHER TEXT NEXT TO IT',score=.99,box=[.1,.1,.9,.9])]
 im,d,rows=scene();before=copy.deepcopy(d);assert refine(im,d,Different(rows),Vision(),rows)==before


def test_horizontal_ocr_fragments_form_one_caption_without_joining_a_distant_column():
 im,d,rows=scene();rows=[dict(text='CITY',score=.99,box=[100,100,180,140]),dict(text='NAME',score=.99,box=[185,103,260,140]),dict(text='OTHER',score=.99,box=[700,100,800,140])]
 result=candidates(im,d,rows);assert len(result)==2 and result[0]['rows'][0]['text']=='CITY NAME'


def test_candidate_next_to_existing_title_fragment_cannot_create_partial_utterance():
 im,d,rows=scene();rows[0]['box']=[620,470,690,510]
 assert candidates(im,d,rows)==[]


def test_covered_words_weak_ocr_and_numbers_are_not_new_utterances():
 im,d,rows=scene();rows=[dict(text='ORIGINAL',score=.99,box=[610,410,790,450]),dict(text='WEAK',score=.89,box=[100,100,300,140]),dict(text='395',score=.99,box=[50,900,80,920])]
 assert candidates(im,d,rows)==[]


@pytest.mark.parametrize('kind',['credits','character_profile','advertisement','cover_gallery','illustration'])
def test_non_story_pages_and_fictional_profile_keep_original_list(kind):
 im,d,rows=scene();d['analysis']['page_context']['classification']['kind']=kind;old=copy.deepcopy(d);v=Vision();assert refine(im,d,Reader(rows),v,rows)==old and v.calls==0


def test_human_verified_page_stays_immutable():
 im,d,rows=scene();d['review']['verified']=True;old=copy.deepcopy(d);v=Vision();assert refine(im,d,Reader(rows),v,rows)==old and v.calls==0


def test_two_unordered_new_utterances_in_one_gap_require_more_evidence_and_are_not_added():
 im,d,rows=scene();rows.append(dict(text='CITY NAME',score=.99,box=[100,250,300,290]));old=copy.deepcopy(d)
 assert refine(im,d,Reader(rows),Vision(),rows)==old


def test_recovery_can_be_undone_and_keeps_human_review_unverified():
 im,d,rows=scene();before=copy.deepcopy(d);refine_page(im,d,Reader(rows),Vision())
 assert d['analysis']['page_context']['status']=='applied' and d['review']['verified'] is False
 assert restore_page_context(d) is True
 assert d['result']==before['result'] and d['analysis']['reading_anchors']==before['analysis']['reading_anchors'] and d['review']==before['review']


@pytest.mark.parametrize('strict',[False,True])
def test_unavailable_model_reverts_entire_stage_and_releases_memory(strict):
 class Broken(Vision):
  def __init__(self):super().__init__();self.strict=strict;self.parked=False
  def _ask(self,*args):raise RuntimeError('offline')
  def park(self):self.parked=True
 im,d,rows=scene();before=copy.deepcopy(d);model=Broken()
 if strict:
  with pytest.raises(RuntimeError):refine_page(im,d,Reader(rows),model)
 else:
  after=refine_page(im,d,Reader(rows),model);assert after['result']==before['result'] and after['analysis']['reading_anchors']==before['analysis']['reading_anchors']
 assert model.parked
