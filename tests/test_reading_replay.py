import copy
import unittest
from tools.bubble_studio.geometry import ordered_result,rectangle
from tools.bubble_studio.reading_replay import reorder

class ReadingReplayTests(unittest.TestCase):
    def document(self):
        result=ordered_result([],[rectangle([70,10,90,30],100,100,.9,margin=0),rectangle([10,10,30,30],100,100,.8,margin=0)],100,100,'rtl','auto')
        return {'result':result,'lab':{'sha256':'image','code_sha256':'original-GPU'},'review':{'flags':['Check region b1']},
            'analysis':{'reading_anchors':{b['id']:{k:b[k] for k in ('x','y','w','h')} for b in result['bubbles']},
                        'text_check':{'regions':[{'region_id':'b1','ocr':[{'text':'Right'}]},{'region_id':'b2','ocr':[{'text':'Left'}]}]}}}

    def test_identity_replay_keeps_exact_result_and_original_source(self):
        doc=self.document();before=copy.deepcopy(doc);new=reorder(doc)
        self.assertEqual(new['result'],doc['result']);self.assertEqual(doc,before)
        self.assertEqual(new['lab']['code_sha256'],'original-GPU')
        self.assertEqual(new['layout_replay']['inference_code_sha256'],'original-GPU')

    def test_changed_direction_updates_ids_ocr_and_flags_together(self):
        doc=self.document();doc['result']['direction']='ltr';new=reorder(doc)
        self.assertEqual(new['result']['bubbles'][0]['confidence'],.8)
        self.assertEqual(new['analysis']['text_check']['regions'][0]['region_id'],'b2')
        self.assertEqual(new['review']['flags'],['Check region b2'])

    def test_absent_or_invalid_anchors_are_rejected(self):
        doc=self.document();doc['analysis'].pop('reading_anchors')
        with self.assertRaises(ValueError):reorder(doc)
        doc=self.document();doc['analysis']['reading_anchors']['b1']['x']=float('nan')
        with self.assertRaises(ValueError):reorder(doc)

    def test_edited_crop_is_not_reinterpreted_as_full_page(self):
        doc=self.document();doc['result']['crop']['w']=.5
        with self.assertRaises(ValueError):reorder(doc)
