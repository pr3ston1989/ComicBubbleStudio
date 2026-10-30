import copy
import pytest
from web.backend.comic_smartview_layout import group_bubbles_by_panel
from tools.bubble_studio.geometry import ordered_result


def blocks(staggered=True,mirror=False):
    return [dict(id=label,panel_id='p1',type='text',x=(.6-.2*i if mirror else .1+.2*i),
                 y=.1+.06*i if staggered else .1,w=.19,h=.1)
            for i,label in enumerate('abc')]


PANEL=dict(id='p1',x=0,y=0,w=1,h=1)


@pytest.mark.parametrize('direction',['ltr','rtl'])
@pytest.mark.parametrize('mirror',[False,True])
@pytest.mark.parametrize('scale',[.5,1])
def test_three_descending_text_blocks_follow_starts_not_overlapping_bottoms(direction,mirror,scale):
    items=blocks(mirror=mirror)
    for b in items:
        for k in ('x','y','w','h'):b[k]*=scale
    original=copy.deepcopy(items)
    assert [b['id'] for b in group_bubbles_by_panel([PANEL],items,direction)]==list('abc')
    assert items==original
    # Real conflict fallbacks keep anchors that were made for a balloon.
    # The actual surviving text classification must reach panel ordering.
    for b in items:
        b.update(name=b['id'],confidence=.9,source='external')
        b['_reading_box']={k:b[k] for k in ('x','y','w','h')}
        b['_reading_box']['type']='bubble'
    result=ordered_result([copy.deepcopy(PANEL)],items,1000,1400,direction,'auto')
    assert [b['name'] for b in result['bubbles']]==list('abc')


@pytest.mark.parametrize('direction',['ltr','rtl'])
def test_aligned_columns_keep_reading_direction(direction):
    assert [b['id'] for b in group_bubbles_by_panel([PANEL],blocks(False),direction)]==list('abc' if direction=='ltr' else 'cba')


def test_mixed_balloons_keep_long_speech_and_short_reply_row_rule():
    items=blocks();items[0]['type']='bubble'
    assert [b['id'] for b in group_bubbles_by_panel([PANEL],items,'rtl')]==list('bac')


def test_two_independent_columns_are_insufficient_to_infer_a_staircase():
    assert [b['id'] for b in group_bubbles_by_panel([PANEL],blocks()[:2],'rtl')]==list('ba')
