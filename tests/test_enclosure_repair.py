import copy
import cv2
import numpy as np
from PIL import Image
from tools.bubble_studio.geometry import contour_box,rectangle
from tools.bubble_studio.enclosure_repair import repair_enclosure,repair_page_enclosures


def example(leak=True,extra_word=False):
    rgb=np.full((600,900,3),80,np.uint8);mask=np.zeros((600,900),np.uint8)
    cv2.ellipse(rgb,(600,220),(120,90),0,0,360,(255,255,255),-1);cv2.ellipse(rgb,(600,220),(120,90),0,0,360,(0,0,0),3)
    cv2.ellipse(mask,(600,220),(120,90),0,0,360,1,-1);cv2.putText(rgb,'HELLO',(548,230),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,0,0),2)
    if leak:cv2.circle(mask,(240,300),130,1,-1);cv2.rectangle(mask,(240,265),(600,295),1,-1)
    bubble=contour_box(mask,(0,0),900,600,.95,epsilon=.1,max_vertices=2048);bubble.update(id='b1',order=1,panel_id='p1')
    text=dict(box=[546,204,640,235],label=1,score=.96);anchor=rectangle(text['box'],900,600,1,margin=0)
    rows=[dict(text='HELLO',score=.99,box=[546/900,204/600,640/900,235/600])]
    if extra_word:rows.append(dict(text='ANOTHER',score=.99,box=[200/900,280/600,280/900,310/600]))
    doc=dict(result=dict(bubbles=[bubble]),analysis=dict(reading_anchors=dict(b1={k:anchor[k] for k in ('x','y','w','h')}),balloons=[dict(supporting_texts=[text])],text_check=dict(regions=[dict(region_id='b1',box=[0,0,900,600],ocr=rows)])),review=dict(verified=False,flags=[]))
    return Image.fromarray(rgb),doc,bubble


def test_major_artwork_leak_is_replaced_by_actual_enclosure_preserving_all_words():
    image,document,bubble=example();region,audit=repair_enclosure(image,document,bubble)
    assert audit and audit['area_ratio']<.60 and audit['stability']>=.985
    assert region['x']>.5 and audit['original_region']==bubble


def test_correct_balloon_and_independent_ocr_outside_repair_are_not_clipped():
    for kwargs in [dict(leak=False),dict(extra_word=True)]:
        image,document,bubble=example(**kwargs)
        assert repair_enclosure(image,document,bubble)==(bubble,None)


def test_no_independent_ocr_and_verified_page_do_not_authorize_repair():
    image,document,bubble=example();document['analysis']['text_check']['regions']=[]
    assert repair_enclosure(image,document,bubble)==(bubble,None)
    document['review']['verified']=True;old=copy.deepcopy(document)
    assert repair_page_enclosures(image,document,None)==old
