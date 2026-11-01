"""Text and ordering safety for native closed-body recovery."""
import copy
from unittest.mock import patch
import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw
from tools.bubble_studio.geometry import contour_box, rectangle
from tools.bubble_studio import closed_body as body

class Reader:
    def __init__(self, text='HELLO'):
        self.text = text
        self.calls = 0
    def read(self, image):
        self.calls += 1
        return [dict(text=self.text, score=.99, box=[.25,.42,.75,.56])]

def page(gap=0):
    image = Image.new('RGB', (2400,3000), 'white')
    draw = ImageDraw.Draw(image)
    draw.rectangle((50,60,1100,1480), outline='black', width=8)
    draw.ellipse((200,200,500,700), outline='black', width=4)
    if gap:
        draw.rectangle((494,447-gap//2,505,447+(gap+1)//2), fill='white')
    draw.text((280,420), 'HELLO', fill='black')
    mask = np.zeros((3000,2400), np.uint8)
    mask[65:1476,55:1096] = 1
    balloon = contour_box(mask,(0,0),2400,3000,.96)
    balloon.update(id='b1', order=1, panel_id='p1')
    panel = rectangle([50,60,1100,1480],2400,3000,.99,margin=0)
    panel['id'] = 'p1'
    anchor = rectangle([270,400,430,480],2400,3000,.96,margin=0)
    anchor = {k:anchor[k] for k in ('x','y','w','h')}
    x,y,xx,yy = body.pixel_box(balloon,image.size)
    word = dict(text='HELLO',score=.99,box=[(275-x)/(xx-x),(415-y)/(yy-y),(425-x)/(xx-x),(455-y)/(yy-y)])
    doc = dict(result=dict(width=2400,height=3000,direction='rtl',layout='auto',
        bubbles=[balloon],panels=[panel],confidence=.96),
        analysis=dict(reading_anchors={'b1':anchor},balloons=[dict(supporting_texts=[
            dict(box=[270,400,430,480],label=1,score=.96)])],
            text_check=dict(mode='review',regions=[dict(region_id='b1',box=[x,y,xx,yy],ocr=[word],uncertain=False)])),
        review=dict(verified=False,flags=[]))
    return image,doc

def test_closed_body_recovery_keeps_words_ids_order_anchors_and_reversible_original():
    image,doc = page()
    before = copy.deepcopy(doc)
    result = body.refine(image,doc,Reader())
    assert 'native_body_error' not in result['analysis']
    assert 'native_body_refinement' in result['analysis']
    old,new = before['result']['bubbles'][0],result['result']['bubbles'][0]
    assert new['w']*new['h'] < old['w']*old['h']*.3
    assert [(b['id'],b['order'],b['panel_id']) for b in result['result']['bubbles']] == [('b1',1,'p1')]
    assert result['result']['direction'] == 'rtl'
    assert result['analysis']['reading_anchors'] == before['analysis']['reading_anchors']
    assert [r['text'] for r in result['analysis']['text_check']['regions'][0]['ocr']] == ['HELLO']
    audit = result['analysis']['native_body_refinement']['changes'][0]
    assert audit['original_region'] == old
    assert audit['original_text_check'] == before['analysis']['text_check']['regions'][0]

def test_small_printed_gap_is_repaired_in_native_pixels_without_tracing_panel():
    image,doc = page(gap=5)
    result = body.refine(image,doc,Reader())
    assert 'native_body_refinement' in result['analysis']
    change = result['analysis']['native_body_refinement']['changes'][0]
    assert change['ink_gap_closing'] >= 5
    assert result['result']['bubbles'][0]['h'] < .2

@pytest.mark.parametrize('text',['NOT THE SAME WORDS',''])
def test_independent_ocr_mismatch_cannot_replace_a_body(text):
    image,doc = page();old = copy.deepcopy(doc)
    assert body.refine(image,doc,Reader(text)) == old

def test_unassigned_words_outside_anchor_cannot_be_discarded_as_background():
    image,doc = page();check = doc['analysis']['text_check']['regions'][0]
    check['ocr'].append(dict(text='ANOTHER UTTERANCE',score=.99,box=[.5,.6,.8,.65]))
    old = copy.deepcopy(doc)
    assert body.refine(image,doc,Reader()) == old

def test_verified_pages_and_free_text_shapes_are_not_changed():
    image,doc = page();doc['review']['verified'] = True;reader = Reader()
    assert body.refine(image,doc,reader) is doc and reader.calls == 0
    doc['review']['verified'] = False
    doc['analysis']['balloons'][0]['supporting_texts'][0]['label'] = 2
    old = copy.deepcopy(doc)
    assert body.refine(image,doc,reader) == old and reader.calls == 0

def test_failure_after_committing_first_body_rolls_back_whole_page():
    image,doc = page()
    proposal = body.propose(image,doc,doc['result']['bubbles'][0],Reader())[0]
    second = rectangle([1500,2000,1800,2100],*image.size,.96,'text',margin=0)
    second.update(id='b2',order=2,panel_id='p1')
    doc['result']['bubbles'].append(second)
    doc['analysis']['reading_anchors']['b2'] = {k:second[k] for k in ('x','y','w','h')}
    old = copy.deepcopy(doc)
    def proposals(im,d,region,checker):
        if region['id'] == 'b1':
            return [proposal]
        assert d['result']['bubbles'][0] == proposal['target']
        raise RuntimeError('failure after first committed body')
    with patch.object(body,'propose',proposals):
        result = body.refine(image,doc,Reader())
    assert result['result'] == old['result']
    assert result['analysis']['reading_anchors'] == old['analysis']['reading_anchors']
    assert result['analysis']['text_check'] == old['analysis']['text_check']
    assert 'native_body_refinement' not in result['analysis']
    assert result['analysis']['native_body_error'] == 'RuntimeError'

def test_every_original_word_box_must_fit_even_when_reread_would_omit_it():
    image,doc = page();old = doc['result']['bubbles'][0]
    evidence = body.own_ocr(doc,old,image.size)
    target = rectangle([270,400,355,480],*image.size,.96,'text',margin=0)
    target.update(id='b1',order=1,panel_id='p1')
    assert body.text_safe(image,doc,target,evidence[1],evidence[2],Reader()) is None

def test_original_transcript_survives_differently_ordered_independent_reread():
    image,doc = page();check = doc['analysis']['text_check']['regions'][0]
    check['ocr'][0]['text'] = 'HELLO WORLD'
    result = body.refine(image,doc,Reader('WORLD HELLO'))
    assert 'native_body_refinement' in result['analysis']
    assert result['analysis']['text_check']['regions'][0]['ocr'][0]['text'] == 'HELLO WORLD'
