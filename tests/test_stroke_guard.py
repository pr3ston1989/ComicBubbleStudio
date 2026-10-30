"""Image-evidence controls for native outline recovery."""
import copy
import cv2
import numpy as np
import pytest
from PIL import Image
from tools.bubble_studio.geometry import contour_box
from tools.bubble_studio.stroke_guard import recover_stroke_outline, recover_page_outlines
from tools.bubble_studio.color_stroke_guard import recover_color_stroke
from tools.bubble_studio.quality_guard import _polygons


def scene(dark=False, complete=False, flaw=None, scale=1, mirrored=False):
    shape = np.zeros((300, 440), np.uint8)
    cv2.ellipse(shape, (280, 120), (100, 60), 0, 0, 360, 1, -1)
    cv2.fillPoly(shape, [np.array([[211, 118], [80, 240], [243, 170]])], 1)
    inside = cv2.erode(shape, np.ones((9, 9), np.uint8))
    rgb = np.full((300, 440, 3), (90, 140, 170), np.uint8)
    stroke, paper = ((255, 0) if dark else (0, 255))
    rgb[shape > 0] = stroke
    rgb[inside > 0] = paper
    for x in (250, 265, 280, 295):
        cv2.rectangle(rgb, (x, 110), (x+5, 125), (stroke,)*3, -1)
    if flaw == 'connected-art':
        cv2.line(rgb, (80, 240), (0, 240), (stroke,)*3, 3)
    if flaw == 'open-outline':
        cv2.rectangle(rgb, (275, 50), (285, 75), (90, 140, 170), -1)
    if flaw == 'second-balloon':
        cv2.circle(rgb, (70, 100), 30, (stroke,)*3, -1)
        cv2.circle(rgb, (70, 100), 25, (paper,)*3, -1)
        cv2.line(rgb, (99, 100), (184, 120), (stroke,)*3, 3)
    if flaw == 'midtone-paper':
        rgb[inside > 0] = (180, 160, 100)
    if flaw == 'small-art-loop':
        cv2.circle(rgb,(280,49),11,(stroke,)*3,2)
    if flaw == 'multiple-ink-branches':
        cv2.line(rgb,(280,61),(280,25),(stroke,)*3,2)
        cv2.line(rgb,(280,179),(280,217),(stroke,)*3,2)
    old = shape if complete else cv2.dilate(inside, np.ones((5, 5), np.uint8))
    if mirrored:
        rgb = cv2.flip(rgb, 1)
        old = cv2.flip(old, 1)
    if scale != 1:
        rgb = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        old = cv2.resize(old, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
    image = Image.fromarray(rgb)
    bubble = contour_box(old, (0, 0), *image.size, .94)
    bubble.update(id='b4', order=4, panel_id='p2')
    texts = [dict(label=1, score=.96, box=[220*scale, 95*scale, 330*scale, 145*scale])]
    return image, bubble, texts


@pytest.mark.parametrize('dark', [False, True])
@pytest.mark.parametrize('mirrored', [False, True])
@pytest.mark.parametrize('scale', [1, 1.5, 2])
def test_actual_closed_ink_tip_is_restored_without_body_or_identity_loss(dark, mirrored, scale):
    image, bubble, texts = scene(dark=dark, mirrored=mirrored, scale=scale)
    before = copy.deepcopy(bubble)
    result, audit = recover_stroke_outline(image, bubble, texts)
    assert audit and audit['mask_preserved'] >= .999
    assert audit['reach'] > 7 and audit['stability'] >= .98
    assert all(result[k] == bubble[k] for k in ['id', 'order', 'panel_id', 'confidence'])
    assert bubble == before


@pytest.mark.parametrize('dark', [False, True])
def test_complete_outline_is_unchanged(dark):
    image, bubble, texts = scene(dark=dark, complete=True)
    result, audit = recover_stroke_outline(image, bubble, texts)
    assert result is bubble and audit is None


@pytest.mark.parametrize('flaw', ['connected-art', 'open-outline', 'second-balloon', 'midtone-paper',
                                  'small-art-loop','multiple-ink-branches'])
def test_ambiguous_or_connected_ink_never_authorizes_an_extension(flaw):
    image, bubble, texts = scene(flaw=flaw)
    result, audit = recover_stroke_outline(image, bubble, texts)
    assert result is bubble and audit is None


@pytest.mark.parametrize('texts', [[], [dict(label=2, score=.99)], [dict(label=1, score=.69)]])
def test_free_text_or_uncertain_text_cannot_become_a_new_outline(texts):
    image, bubble, _ = scene()
    result, audit = recover_stroke_outline(image, bubble, texts)
    assert result is bubble and audit is None


@pytest.mark.parametrize('scale',[1,1.5,2])
@pytest.mark.parametrize('mirrored',[False,True])
def test_chromatic_stroke_is_recovered_with_the_same_native_safeguards(scale,mirrored):
    image,bubble,texts=scene(scale=scale,mirrored=mirrored)
    rgb=np.asarray(image).copy();black=np.all(rgb==0,axis=2)
    rgb[black]=(22,65,100)
    result,audit=recover_color_stroke(Image.fromarray(rgb),bubble,texts)
    assert audit and audit['mask_preserved']>=.999 and audit['stability']>=.98
    assert audit['method']=='native-rgb-isolated-ink-enclosure'
    assert all(result[k]==bubble[k] for k in ('id','order','panel_id','confidence'))


@pytest.mark.parametrize('flaw',['connected-art','open-outline','second-balloon','small-art-loop','multiple-ink-branches'])
def test_color_matching_does_not_bypass_the_topological_guards(flaw):
    image,bubble,texts=scene(flaw=flaw)
    result,audit=recover_color_stroke(image,bubble,texts)
    assert result is bubble and audit is None


def page_scene():
    from tools.bubble_studio.geometry import rectangle
    image, bubble, texts = scene()
    anchor = rectangle(texts[0]['box'], *image.size, .9, margin=0)
    doc = dict(result=dict(bubbles=[bubble],direction='rtl'),
               review=dict(verified=False,flags=[]),
               analysis=dict(reading_anchors={bubble['id']:{k:anchor[k] for k in ('x','y','w','h')}},
                             balloons=[dict(supporting_texts=texts)]))
    return image,doc


def test_page_guard_keeps_reading_identity_and_diagnostics_with_reversible_original():
    image,doc=page_scene(); before=copy.deepcopy(doc)
    recover_page_outlines(image,doc)
    assert doc['analysis']['reading_anchors']==before['analysis']['reading_anchors']
    assert doc['analysis']['balloons']==before['analysis']['balloons']
    assert doc['result']['direction']=='rtl'
    assert doc['analysis']['stroke_outline_recovery'][0]['original_region']==before['result']['bubbles'][0]
    assert all(doc['result']['bubbles'][0][k]==before['result']['bubbles'][0][k]
               for k in ('id','order','panel_id','confidence'))


@pytest.mark.parametrize('reason',['verified','missing-anchor','ambiguous-evidence','mismatched-evidence'])
def test_page_guard_cannot_modify_verified_or_unbound_regions(reason):
    image,doc=page_scene()
    if reason=='verified':doc['review']['verified']=True
    if reason=='missing-anchor':doc['analysis']['reading_anchors']={}
    if reason=='ambiguous-evidence':doc['analysis']['balloons']*=2
    if reason=='mismatched-evidence':doc['analysis']['balloons'][0]['supporting_texts'][0]['box'][0]+=3
    before=copy.deepcopy(doc);recover_page_outlines(image,doc)
    assert doc==before


@pytest.mark.parametrize('polygon',[False,True])
def test_page_guard_rejects_tip_crossing_neighbouring_text_or_contour(polygon):
    from tools.bubble_studio.geometry import rectangle
    image,doc=page_scene()
    other=rectangle([75,231,88,245],*image.size,.9,'text',margin=0)
    other.update(id='b8',order=8)
    if polygon:
        mask=np.zeros((image.height,image.width),np.uint8);mask[231:246,75:89]=1
        other=contour_box(mask,(0,0),*image.size,.9);other.update(id='b8',order=8)
    doc['result']['bubbles'].append(other)
    before=copy.deepcopy(doc);recover_page_outlines(image,doc)
    assert doc==before
