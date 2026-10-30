import copy
from PIL import Image
import pytest
from tools.bubble_studio.publishing_filter import publishing_evidence,refine_publishing
from tools.bubble_studio.page_context import restore_page_context

def rows(*texts):return [dict(text=t,score=.99,box=[0,i*20,800,i*20+18]) for i,t in enumerate(texts)]

def test_catalog_requires_independent_markers_not_an_isolated_next_issue():
    assert publishing_evidence(rows('NEXT ISSUE')) is None
    assert publishing_evidence(rows('DISPATCH','HIGHLIGHTED TITLES','NEXT ISSUE','FIRST ISSUE','LEARN MORE ONLINE'))['category']=='catalog'

def test_real_interview_requires_a_heading_and_multiple_publishing_terms():
    assert publishing_evidence(rows('CONVERSATION WITH THE KING','A writer is in trouble')) is None
    assert publishing_evidence(rows('CONVERSATION WITH THE CREATORS','Writer and artist','Copyright, published monthly'))['category']=='creator_interview'

@pytest.mark.parametrize('heading',['PART THREE','CHAPTER 12','Part II: STEEL'])
def test_chapter_heading_protects_a_page_with_credits(heading):
    assert publishing_evidence(rows('CONVERSATION WITH THE CREATORS','Writer and artist, published monthly',heading)) is None

class Checker:
    def locate_context(self,image):return rows('DISPATCH','HIGHLIGHTED TITLES','NEXT ISSUE','FIRST ISSUE','LEARN MORE ONLINE')

class Semantic:
    def __init__(self,category):self.category=category
    def _ask(self,*args):return dict(category=self.category)

def doc():
    return dict(result=dict(bubbles=[dict(id='b1',confidence=.9,order=1)],confidence=.9),
        analysis=dict(reading_anchors={'b1':dict(x=.1,y=.1,w=.2,h=.1)},page_context=dict(classification=dict(kind='mixed'))),
        review=dict(verified=False,flags=['Check b1']))

def test_audit_is_reversible_and_does_not_change_human_verification():
    d=doc();original=copy.deepcopy(d)
    refine_publishing(Image.new('RGB',(1000,1000)),d,Checker(),Semantic('publisher_catalog'))
    assert not d['result']['bubbles'] and restore_page_context(d)
    assert d['result']==original['result'] and d['review']==original['review']

@pytest.mark.parametrize('answer',['story_or_mixed','uncertain',None,0,'false'])
def test_story_or_invalid_category_keeps_every_detection(answer):
    d=doc();original=copy.deepcopy(d)
    assert refine_publishing(Image.new('RGB',(1000,1000)),d,Checker(),Semantic(answer))==original

def test_verified_pages_are_immutable():
    d=doc();d['review']['verified']=True;original=copy.deepcopy(d)
    assert refine_publishing(Image.new('RGB',(1000,1000)),d,Checker(),Semantic('publisher_catalog'))==original
