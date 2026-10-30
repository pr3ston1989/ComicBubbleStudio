import unittest
from web.backend.comic_smartview_layout import order_boxes_by_cuts,group_bubbles_by_panel

def region(name,x,y,w,h,**extra):return dict(id=name,name=name,x=x,y=y,w=w,h=h,**extra)

class ReadingLayout233Tests(unittest.TestCase):
    def test_body_containment_is_guarded_even_when_text_anchors_do_not_overlap(self):
        from tools.bubble_studio.geometry import ordered_result
        panel=region('p1',0,0,1,1,confidence=.9,type='bubble',source='external')
        outer=region('outer',.1,.2,.6,.4,confidence=.9,type='text',source='external')
        inner=region('inner',.2,.22,.25,.1,confidence=.8,type='text',source='external')
        outer['_reading_box']=region('oa',.6,.2,.1,.04)
        inner['_reading_box']=region('ia',.2,.23,.1,.06)
        result=ordered_result([panel],[outer,inner],100,100,'ltr','auto')
        self.assertEqual([b['name'] for b in result['bubbles']],['outer','inner'])

    def test_nested_duplicate_anchor_does_not_jump_before_outer_utterance(self):
        panel=region('p1',0,0,1,1)
        boxes=[region('outer',.1,.2,.6,.4,panel_id='p1'),region('inner',.3,.3,.2,.1,panel_id='p1')]
        actual=group_bubbles_by_panel([panel],boxes,'rtl')
        self.assertEqual([b['name'] for b in actual],['outer','inner'])

    def test_short_text_inside_height_of_long_text_reads_on_its_rtl_side(self):
        panel=region('p1',0,0,1,1)
        boxes=[region('long',.1,.2,.25,.3,panel_id='p1'),region('short',.7,.33,.2,.05,panel_id='p1')]
        self.assertEqual([b['name'] for b in group_bubbles_by_panel([panel],boxes,'rtl')],['short','long'])

    def test_mirrored_case_reads_from_left_in_western_comic(self):
        panel=region('p1',0,0,1,1)
        boxes=[region('long',.7,.2,.25,.3,panel_id='p1'),region('short',.1,.33,.2,.05,panel_id='p1')]
        self.assertEqual([b['name'] for b in group_bubbles_by_panel([panel],boxes,'ltr')],['short','long'])

    def test_two_rows_are_not_inferred_as_four_koma_from_small_y_gap(self):
        boxes=[region(str((row,col)),.05+col*.31,.1+row*.31,.27,.30) for row in range(2) for col in range(3)]
        self.assertEqual([b['name'] for b in order_boxes_by_cuts(boxes,'ltr',page_aspect=1.5)],
                         [str((row,col)) for row in range(2) for col in range(3)])

    def test_top_unframed_dialogue_precedes_the_entire_detected_grid(self):
        panels=[region('p'+str(row*3+col),.05+col*.31,.3+row*.31,.27,.30) for row in range(2) for col in range(3)]
        bubbles=[region('bottom'+str(i),p['x']+.02,p['y']+.02,.1,.1,panel_id=p['id']) for i,p in enumerate(panels)]
        bubbles.extend([region('top-left',.1,.02,.1,.05,panel_id=None),region('top-right',.8,.04,.1,.05,panel_id=None)])
        actual=group_bubbles_by_panel(panels,bubbles,'ltr',page_aspect=1.5)
        self.assertEqual([b['name'] for b in actual[:2]],['top-left','top-right'])
