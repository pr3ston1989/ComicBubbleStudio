import copy
import pytest
from PIL import Image
from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.strip_reader import strip_columns, refine_strips
from tools.bubble_studio.page_context import restore_page_context

def scene(direction='rtl'):
    panels=[];bubbles=[];anchors={}
    for col,x in enumerate((.05,.55)):
        for row in range(4):
            panel=dict(x=x,y=.12+row*.21,w=.4,h=.18,id=f'p{col*4+row+1}')
            panels.append(panel)
            b=dict(rectangle([(x+.15)*1000,(panel['y']+.04)*1000,(x+.3)*1000,(panel['y']+.10)*1000],1000,1000,.95,'text',0),id=f'b{len(bubbles)+1}',order=len(bubbles)+1,panel_id=panel['id'])
            bubbles.append(b);anchors[b['id']]={k:b[k] for k in ('x','y','w','h')}
    return dict(result=dict(width=1000,height=1000,direction=direction,layout='auto',panels=panels,bubbles=bubbles,confidence=.95),analysis=dict(reading_anchors=anchors),review=dict(verified=False,flags=['Check b1']))

class Semantic:
    def __init__(self,answer=True):self.answer=answer;self.calls=0
    def _ask(self,images,prompt):self.calls+=1;return dict(four_panel_strips=self.answer)

class Checker:
    def __init__(self):self.reviewed=False
    def locate_context(self,image):
        return [dict(box=[60,80,300,105],text='A proper strip title',score=.99),
                dict(box=[650,80,940,105],text='Another strip title',score=.99),
                dict(box=[800,970,840,985],text='123',score=.99)]
    def review(self,image,doc):
        self.reviewed=True
        doc['analysis']['text_check']=dict(mode='review',regions=[dict(region_id=b['id'],ocr=[]) for b in doc['result']['bubbles']])

@pytest.mark.parametrize('direction',['ltr','rtl'])
def test_each_title_is_followed_by_its_entire_strip_with_continuous_ids(direction):
    doc=scene(direction);original=copy.deepcopy(doc);checker=Checker()
    result=refine_strips(Image.new('RGB',(1000,1000)),doc,checker,Semantic())
    bubbles=result['result']['bubbles'];assert len(bubbles)==10 and checker.reviewed
    assert [b['id'] for b in bubbles]==[f'b{i+1}' for i in range(10)]
    assert [b['order'] for b in bubbles]==list(range(1,11))
    first,last=(.55,.05) if direction=='rtl' else (.05,.55)
    assert all(first<=b['x']<=first+.4 for b in bubbles[:5])
    assert all(last<=b['x']<=last+.4 for b in bubbles[5:])
    assert bubbles[0]['y']<.12 and bubbles[5]['y']<.12
    assert set(result['analysis']['reading_anchors'])=={b['id'] for b in bubbles}
    assert {r['region_id'] for r in result['analysis']['text_check']['regions']}==set(result['analysis']['reading_anchors'])
    assert restore_page_context(result) and result['result']==original['result']

@pytest.mark.parametrize('answer',[False,None,1,'true'])
def test_geometry_alone_cannot_reorder_an_ordinary_grid(answer):
    doc=scene();original=copy.deepcopy(doc)
    assert refine_strips(Image.new('RGB',(1000,1000)),doc,Checker(),Semantic(answer))==original

@pytest.mark.parametrize('layout',['rows','single'])
def test_explicit_user_layout_is_preserved_without_query(layout):
    doc=scene();doc['result']['layout']=layout;original=copy.deepcopy(doc);semantic=Semantic()
    assert refine_strips(Image.new('RGB',(1000,1000)),doc,Checker(),semantic)==original
    assert semantic.calls==0

def test_unassigned_story_text_prevents_the_reorder_instead_of_disappearing():
    doc=scene();b=dict(rectangle([450,400,520,450],1000,1000,.9,'text',0),id='b9',order=9,panel_id=None)
    doc['result']['bubbles'].append(b);doc['analysis']['reading_anchors']['b9']={k:b[k] for k in ('x','y','w','h')};original=copy.deepcopy(doc)
    assert refine_strips(Image.new('RGB',(1000,1000)),doc,Checker(),Semantic())==original

def test_human_verification_is_immutable():
    doc=scene();doc['review']['verified']=True;original=copy.deepcopy(doc);semantic=Semantic()
    assert refine_strips(Image.new('RGB',(1000,1000)),doc,Checker(),semantic)==original
    assert semantic.calls==0

def test_unequal_or_incomplete_columns_are_not_guessed():
    doc=scene();doc['result']['panels'].pop()
    assert not strip_columns(doc['result'])
