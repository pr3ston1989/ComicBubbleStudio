import copy
import pytest
from tools.bubble_studio.regression_gate import compare_text_additions


def case():
    old=[dict(id=f'b{i+1}',order=i+1,panel_id=None,type='text',confidence=.9,source='external',x=.1+i*.4,y=.1,w=.1,h=.1) for i in range(2)]
    added=dict(old[0],id='b2',order=2,x=.3,y=.5)
    before=dict(lab=dict(sha256='image'),review=dict(verified=False),
                result=dict(width=1000,height=1000,direction='ltr',panels=[],bubbles=old,confidence=.9),
                analysis=dict(reading_anchors={'b1':dict(x=.1),'b2':dict(x=.5)},
                              text_check=dict(regions=[dict(region_id='b2',ocr=[dict(text='Protected words')])])))
    after=copy.deepcopy(before)
    after['result']['bubbles']=[old[0].copy(),added.copy(),dict(old[1],id='b3',order=3)]
    after['analysis']['reading_anchors']={'b1':dict(x=.1),'b3':dict(x=.5),'b2':dict(x=.3)}
    after['analysis']['text_check']['regions'][0]['region_id']='b3'
    rule=dict(preserved_regions={'b1':'b1','b2':'b3'},additions=[dict(region=added.copy(),image_sha256='image',native_ocr=[dict(box=[310,510,390,590],score=.99,text='Actual words here')])])
    return before,after,rule


def test_reviewed_addition_keeps_geometry_order_anchors_and_words():
    assert compare_text_additions(*case())==[]


@pytest.mark.parametrize('failure',['clipped','missing-evidence','wrong-image','unapproved-shape','old-geometry','old-order','old-anchor','old-ocr','incomplete-map','duplicate-map','verified'])
def test_addition_approval_does_not_authorize_other_changes(failure):
    before,after,rule=case()
    if failure=='clipped':
        after['result']['bubbles'][1]['w']=.01
        rule['additions'][0]['region']['w']=.01
    elif failure=='missing-evidence':rule['additions'][0]['native_ocr']=[]
    elif failure=='wrong-image':rule['additions'][0]['image_sha256']='different'
    elif failure=='unapproved-shape':after['result']['bubbles'][1]['x']+=.01
    elif failure=='old-geometry':after['result']['bubbles'][0]['w']+=.01
    elif failure=='old-order':after['result']['bubbles'][0]['order']=4
    elif failure=='old-anchor':after['analysis']['reading_anchors']['b1']['x']+=.01
    elif failure=='old-ocr':after['analysis']['text_check']['regions'][0]['ocr']=[]
    elif failure=='incomplete-map':rule['preserved_regions'].pop('b1')
    elif failure=='duplicate-map':rule['preserved_regions']['b1']='b3'
    elif failure=='verified':after['review']['verified']=True
    assert compare_text_additions(before,after,rule)
