import copy
import json
from PIL import Image
import pytest
from tools.bubble_studio.page_context import SemanticPage,omission_allowed,parse_answer,restore_page_context,region_candidate
from tools.bubble_studio.geometry import rectangle


def document():
    b=dict(rectangle([20,20,180,80],1000,1000,.9,'text',margin=0),id='b1',order=1,panel_id=None)
    return dict(result=dict(width=1000,height=1000,direction='ltr',layout='auto',panels=[],bubbles=[b],confidence=.9),
        analysis=dict(reading_anchors={'b1':{k:b[k] for k in ('x','y','w','h')}},text_check=dict(mode='review',regions=[dict(region_id='b1',box=[20,20,180,80],ocr=[dict(text='I can hear you.',score=.99)])])),
        review=dict(verified=False,flags=['Preserved observation']))


class Checker:
    def __init__(self,rows=()):self.rows=list(rows)
    def locate_context(self,image):return self.rows
    def review(self,image,doc):
        doc['analysis']['text_check']=dict(mode='review',regions=[dict(region_id=b['id'],ocr=[]) for b in doc['result']['bubbles']]);return doc


class FakeSemantic(SemanticPage):
    def __init__(self,kind,story=False):
        self.kind=kind;self.story=story;self.calls=[];self.provenance={'test':'controlled model outputs'};self.strict=True
    def classify(self,image):return dict(kind=self.kind,contains_readable_story=self.story)
    def structured(self,image,rows):return {'groups':[]}
    def region_role(self,image,bubble):return dict(role='uncertain',enclosure='uncertain')


@pytest.mark.parametrize('kind',['cover_gallery','advertisement'])
def test_editorial_pages_are_reversible_and_never_marked_verified(kind):
    doc=document();old=copy.deepcopy(doc);reader=FakeSemantic(kind)
    reader.review(Image.new('RGB',(1000,1000)),doc,Checker())
    assert not doc['result']['bubbles'] and not doc['review']['verified']
    assert doc['analysis']['page_context']['original']==old
    assert restore_page_context(doc)
    assert doc['result']==old['result'] and doc['analysis']['reading_anchors']==old['analysis']['reading_anchors']
    assert doc['review']==old['review']


@pytest.mark.parametrize('kind',['credits','illustration','character_profile'])
def test_page_kind_alone_cannot_delete_possible_story_headings(kind):
    doc=document();old=copy.deepcopy(doc)
    FakeSemantic(kind).review(Image.new('RGB',(1000,1000)),doc,Checker())
    assert doc['result']==old['result']
    assert not restore_page_context(doc)


def test_human_verified_pages_are_immutable():
    doc=document();doc['review']['verified']=True;old=copy.deepcopy(doc)
    FakeSemantic('advertisement').review(Image.new('RGB',(1000,1000)),doc,Checker())
    assert doc==old


@pytest.mark.parametrize('role',['mechanical_sound','physical_sign','editorial'])
def test_closed_balloon_or_caption_protects_its_words_from_omission(role):
    for enclosure in ['balloon','caption','uncertain']:
        assert not omission_allowed(dict(role=role,enclosure=enclosure),[dict(text='Writer and editor',score=.99)])


def test_editorial_label_requires_independent_credit_markers():
    value=dict(role='editorial',enclosure='none')
    assert not omission_allowed(value,[dict(text='PART THREE: STEEL',score=.99)])
    assert omission_allowed(value,[dict(text='Jason Writer; Juan Artist; Becca Letterer',score=.99)])


def test_punctuation_and_failed_ocr_cannot_authorize_deletion():
    value=dict(role='mechanical_sound',enclosure='none')
    assert not omission_allowed(value,[dict(text='!!!',score=.99)])
    assert not omission_allowed(value,[dict(text='GRIP',score=.2)])


def test_contour_protects_narrow_vocalization_and_location_caption():
    b=document()['result']['bubbles'][0]
    b['type']='bubble';b['polygons']=[[dict(x=0,y=0),dict(x=1,y=0),dict(x=1,y=1)]]
    for text in ['S S S','V ZZZZ','G-FORCE U.S.A. HQ']:
        assert not region_candidate(b,b,[dict(text=text,score=.99)])


@pytest.mark.parametrize('mutation',['result','snapshot','policy','verified'])
def test_external_policy_rejects_unreviewed_context_changes(mutation):
    from tools.bubble_studio.regression_gate import compare_context_change,frozen_digest
    old=document();old['lab']={'sha256':'image-identity'};doc=copy.deepcopy(old)
    FakeSemantic('advertisement').review(Image.new('RGB',(1000,1000)),doc,Checker())
    rule=dict(image_sha256='image-identity',baseline_result_sha256=frozen_digest(old['result']),
        approved_result_sha256=frozen_digest(doc['result']),visual_review='review.json',reason='Visually reviewed')
    assert not compare_context_change(old,doc,rule)
    if mutation=='result':doc['result']['bubbles']=old['result']['bubbles']
    if mutation=='snapshot':doc['analysis']['page_context']['original']['result']['panels']=[{}]
    if mutation=='policy':rule.pop('visual_review')
    if mutation=='verified':doc['review']['verified']=True
    assert compare_context_change(old,doc,rule)


def test_model_failure_rolls_back_every_partial_change():
    doc=document();old=copy.deepcopy(doc);reader=FakeSemantic('advertisement');reader.strict=False
    checker=Checker();checker.review=lambda image,document:(_ for _ in ()).throw(RuntimeError('test failure'))
    result=reader.review(Image.new('RGB',(1000,1000)),doc,checker)
    assert result['result']==old['result']
    assert result['analysis']['page_context']['status']=='unavailable'


def test_editor_context_restore_can_be_undone_and_redone():
    from tools.bubble_studio.review import Reviewer
    doc=document();old=copy.deepcopy(doc)
    FakeSemantic('advertisement').review(Image.new('RGB',(1000,1000)),doc,Checker())
    filtered=copy.deepcopy(doc)
    editor=Reviewer.__new__(Reviewer);editor.index=0;editor.documents=[doc]
    editor.undo_stack=[];editor.redo_stack=[];editor.load_page=lambda:None
    editor.restore_filtered();assert editor.documents[0]['result']==old['result']
    editor.undo();assert editor.documents[0]==filtered
    editor.redo();assert editor.documents[0]['result']==old['result']


@pytest.mark.parametrize('value',[None,False,'[]','not JSON','{"kind":'])
def test_invalid_model_response_cannot_be_executed_or_applied(value):
    assert parse_answer(value) is None
