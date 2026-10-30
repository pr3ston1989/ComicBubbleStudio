"""Meaningful regression cases: ordering, true-text recovery and evaluation."""
import copy
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.bubble_studio.geometry import ordered_result, rectangle
from tools.bubble_studio.evaluate import compare_page
from tools.bubble_studio.textcheck import TextCheck, recover_panel_dialogue, catalog_page
from web.backend.comic_smartview_layout import order_boxes_by_cuts, group_bubbles_by_panel
from web.backend.comic_bubble_package import validate_result
from tools.bubble_studio.config import series_settings


def box(name,x,y,w=.2,h=.2):
    return dict(name=name,x=x,y=y,w=w,h=h,confidence=.9,type='bubble')


class OrderTests(unittest.TestCase):
    def test_supplied_chapter_updates_tree_defaults_to_rtl(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            root=Path(folder)
            book=root/'Weekly Viz, ShonenJump and MangaPlus Chapter Updates'/'Series'/'chapter.cbz'
            self.assertEqual(series_settings(book,root)['direction'],'rtl')
            self.assertEqual(series_settings(root/'Manhua'/'book.cbz',root)['direction'],'ltr')

    def test_equal_pixel_gutters_on_portrait_page_use_rows(self):
        b=[box('tl',.1,.1,.4,.4),box('tr',.6,.1,.4,.4),box('bl',.1,.55,.4,.4),box('br',.6,.55,.4,.4)]
        result=ordered_result([],copy.deepcopy(b),100,200,'ltr','auto')
        self.assertEqual([x['name'] for x in result['bubbles']],['tl','tr','bl','br'])

    def test_sparse_diagonal_bubbles_do_not_imply_vertical_strips(self):
        b=[box('top',.75,.06,.1,.03),box('bottom',.31,.4,.15,.05)]
        self.assertEqual([x['name'] for x in order_boxes_by_cuts(b,'ltr')],['top','bottom'])

    def test_silent_panels_preserve_structure(self):
        panels=[dict(box('silent',0,0,.3,.3),id='p1'),dict(box('top',.6,0,.4,.3),id='p2')]
        b=[dict(box('speech',.7,.05,.1,.05),panel_id='p2'),dict(box('narration',.2,.4,.2,.1),panel_id=None)]
        self.assertEqual([x['name'] for x in group_bubbles_by_panel(panels,b,'ltr')],['speech','narration'])

    def test_explicit_four_koma_columns_remain_available(self):
        b=[box('tl',0,0),box('tr',.6,0),box('bl',0,.5),box('br',.6,.5)]
        self.assertEqual([x['name'] for x in order_boxes_by_cuts(b,'rtl',layout='columns')],['tr','br','tl','bl'])

    def test_slanted_panel_boxes_do_not_absorb_bottom_row(self):
        b=[box('right-tall',.77,.46,.18,.47),box('bottom-right',.43,.76,.57,.24),
           box('bottom-left',0,.72,.50,.27),box('middle-left',0,.51,.80,.29)]
        self.assertEqual([x['name'] for x in order_boxes_by_cuts(b,'rtl')],
                         ['right-tall','middle-left','bottom-right','bottom-left'])

    def test_tail_does_not_change_panel_assignment(self):
        panels=[box('top',0,0,1,.4),box('bottom',0,.5,1,.5)]
        b=box('long-tail',.1,.1,.3,.85)
        b['_reading_box']=box('text',.15,.15,.2,.1)
        result=ordered_result(panels,[b],100,200,'ltr','rows')
        self.assertEqual(result['bubbles'][0]['panel_id'],'p1')
        self.assertNotIn('_reading_box',result['bubbles'][0])
        self.assertEqual(result['bubbles'][0]['h'],.85)
        validate_result(result)

    def test_overlapping_middle_background_does_not_precede_top_right_frame(self):
        b=[box('top-left',.04,.02,.48,.31),box('middle',.12,.18,.88,.43),
           box('top-right',.47,.02,.50,.26),box('middle-alt',0,.25,.95,.42),
           box('bottom-left',.04,.56,.47,.42),box('bottom-right',.4,.51,.58,.46)]
        order=[x['name'] for x in order_boxes_by_cuts(b,'ltr')]
        self.assertLess(order.index('top-right'),order.index('middle'))


class EvaluationTests(unittest.TestCase):
    def test_order_inversions_are_measured_separately_from_perfect_masks(self):
        b=[box('a',0,0),box('b',.4,0),box('c',.7,.5)]
        ref={'width':100,'height':100,'direction':'ltr','bubbles':b}
        pred={**ref,'bubbles':list(reversed(b))}
        score=compare_page(ref,pred)
        self.assertEqual(score['matched_at_iou_50'],3)
        self.assertEqual(score['order_inversions'],3)
        self.assertEqual(score['matched_order_agreement'],0)

    def test_empty_pages_do_not_report_perfect_order(self):
        r={'width':100,'height':100,'direction':'rtl','bubbles':[]}
        self.assertIsNone(compare_page(r,r)['matched_order_agreement'])


class FakeOCR:
    latin_dialogue=staticmethod(TextCheck.latin_dialogue)
    def __init__(self,lines=None): self.lines=lines or []
    def locate(self,image): return self.lines
    def read(self,image): return [{'text':'I can hear you.','score':.98}]


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.image=Image.new('RGB',(600,800),'white')
        self.existing=[rectangle([20,20,120,120],600,800,.95)]

    def test_frameless_thought_is_retained_as_text_without_changing_existing(self):
        text={'box':[300,200,500,260],'label':2,'score':.95}
        original=copy.deepcopy(self.existing)
        recovered,audit=recover_panel_dialogue(FakeOCR(),self.image,[text],self.existing,[])
        self.assertEqual(len(recovered),1)
        self.assertEqual(recovered[0]['type'],'text')
        self.assertFalse(recovered[0].get('polygons'))
        self.assertEqual(self.existing,original)
        self.assertEqual(audit[0]['reason'],'frameless-dialogue')

    def test_ocr_can_recover_without_any_detector_proposal(self):
        lines=[dict(box=[300,200,500,220],text='I can hear you.',score=.98,label=2,origin='ocr')]
        recovered,_=recover_panel_dialogue(FakeOCR(lines),self.image,[],self.existing,[])
        self.assertEqual(len(recovered),1)

    def test_no_duplicate_inside_existing_region(self):
        text={'box':[30,30,100,100],'label':2,'score':.95}
        recovered,_=recover_panel_dialogue(FakeOCR(),self.image,[text],self.existing,[])
        self.assertEqual(recovered,[])

    def test_isolated_effect_and_illustration_title_are_not_recovered(self):
        self.assertFalse(TextCheck.latin_dialogue([dict(text='SPLASH!',score=.99)]))
        self.assertFalse(TextCheck.latin_dialogue([dict(text='CHRP CHRP CHRP',score=.99)]))
        self.assertFalse(TextCheck.latin_dialogue([dict(text='これは私の考えです。',score=.99)]))
        text={'box':[300,200,500,260],'label':2,'score':.95}
        recovered,_=recover_panel_dialogue(FakeOCR(),self.image,[text],[],[])
        self.assertEqual(recovered,[])

    def test_catalog_recovery_blocker_requires_multiple_independent_markers(self):
        self.assertTrue(catalog_page([dict(text='DELUXE EDITION'),dict(text='ALL RIGHTS RESERVED')]))
        self.assertFalse(catalog_page([dict(text='ALL RIGHTS RESERVED')]))
        self.assertFalse(catalog_page([dict(text='I can hear you!')]))


if __name__=='__main__': unittest.main()
