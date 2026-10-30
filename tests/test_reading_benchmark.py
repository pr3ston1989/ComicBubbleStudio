import copy
import unittest
from tools.bubble_studio.reading_benchmark import score_page,compare_evaluations

def box(name,x,y,w=.2,h=.2,order=1):return dict(id=name,x=x,y=y,w=w,h=h,order=order,type='text')
class FullPageReadingTests(unittest.TestCase):
    def setUp(self):
        self.ref={'complete':True,'image_sha256':'source','direction':'ltr','sha_prefix':'source','name':'Page',
                  'utterances':[{'label':'First','points':[[.2,.2]]},{'label':'Second','points':[[.7,.2]]}]}
        self.doc={'lab':{'sha256':'source'},'result':{'direction':'ltr','bubbles':[box('b1',.1,.1),box('b2',.6,.1,order=2)]}}
    def test_complete_page_has_no_missing_extra_or_order_errors(self):
        result=score_page(self.ref,self.doc)
        self.assertTrue(result['complete_reading_success']);self.assertEqual(result['matched_stops'],2)
    def test_extra_sign_is_counted_even_if_all_real_words_are_present(self):
        self.doc['result']['bubbles'].append(box('b3',.4,.7,order=3))
        result=score_page(self.ref,self.doc)
        self.assertEqual(result['extra_regions'],['b3']);self.assertFalse(result['complete_reading_success'])
    def test_single_large_artwork_mask_cannot_match_two_utterances(self):
        self.doc['result']['bubbles']=[box('b1',0,0,w=1,h=1)]
        result=score_page(self.ref,self.doc)
        self.assertEqual(result['matched_stops'],1);self.assertEqual(len(result['missing']),1)
    def test_reversed_sequence_is_measured_after_geometry_matching(self):
        a,b=self.doc['result']['bubbles'];self.doc['result']['bubbles']=[dict(b,id='b1',order=1),dict(a,id='b2',order=2)]
        result=score_page(self.ref,self.doc)
        self.assertEqual(result['order_inversions'],1);self.assertEqual(result['matched_stops'],2)
    def test_connected_lobes_require_all_reference_points(self):
        self.ref['utterances'][0]['points'].append([.2,.6])
        result=score_page(self.ref,self.doc);self.assertEqual(result['missing'][0]['utterance'],1)
    def test_negative_page_does_not_hide_false_stops(self):
        self.ref['utterances']=[]
        result=score_page(self.ref,self.doc)
        self.assertEqual(len(result['extra_regions']),2);self.assertEqual(result['order_pairs'],0)
    def test_excess_artwork_is_separate_from_reading_success(self):
        self.ref['utterances'][0]['exclude_points']=[[.15,.15]]
        result=score_page(self.ref,self.doc)
        self.assertTrue(result['complete_reading_success']);self.assertEqual(len(result['outline_exclusion_failures']),1)
    def test_partial_reference_and_different_image_are_rejected(self):
        self.ref['complete']=False
        with self.assertRaises(ValueError):score_page(self.ref,self.doc)
        self.ref['complete']=True;self.doc['lab']['sha256']='other'
        with self.assertRaises(ValueError):score_page(self.ref,self.doc)

    def test_comparison_blocks_changed_truth_and_new_errors(self):
        page=score_page(self.ref,self.doc)
        before={'reference_sha256':'gold','pages':[page]};after=copy.deepcopy(before)
        self.assertTrue(compare_evaluations(before,after)['passed'])
        after['reference_sha256']='other'
        self.assertFalse(compare_evaluations(before,after)['passed'])
        after=copy.deepcopy(before);after['pages'][0]['extra_regions']=['new-false-stop']
        self.assertFalse(compare_evaluations(before,after)['passed'])
