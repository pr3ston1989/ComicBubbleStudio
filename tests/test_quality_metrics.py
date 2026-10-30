import copy
import json
import tempfile
import unittest
from pathlib import Path
from tools.bubble_studio.quality_metrics import measure,geometry_digest,compare_metrics
from tools.bubble_studio.regression_gate import compare_content_removals,compare


class QualityMetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name)
        self.doc={'lab':{'sha256':'image'},'result':{'width':100,'height':100,'direction':'ltr','bubbles':[
            dict(id='b1',order=1,type='text',x=.1,y=.1,w=.2,h=.2),
            dict(id='b2',order=2,type='text',x=.6,y=.1,w=.2,h=.2)]}}
        self.ref={'scope':'All test pages','policy':'test','pages':[{'sha_prefix':'image','image_sha256':'image',
            'name':'page','complete':True,'direction':'ltr','utterances':[
                {'label':'A','points':[[.2,.2]]},{'label':'B','points':[[.7,.2]]}]}]}
        self.contours={'pages':[{'sha_prefix':'image','image_sha256':'image','size':[100,100],
            'regions':[{'geometry_sha256':geometry_digest(r),'accepted':True} for r in self.doc['result']['bubbles']]}]}
    def score(self):
        (self.folder/'000-image.json').write_text(json.dumps(self.doc),encoding='utf8')
        return measure(self.ref,self.contours,self.folder)
    def test_complete_and_negative_pages(self):
        result=self.score();self.assertEqual(result['overall']['combined_estimate'],1)
        self.ref['pages'][0]['utterances']=[]
        result=self.score();self.assertEqual(result['overall']['detection_f1'],0)
        self.assertEqual(result['overall']['false_positives'],2)
        self.doc['result']['bubbles']=[]
        result=self.score();self.assertIsNone(result['overall']['combined_estimate'])
        self.assertEqual(result['overall']['fully_accepted_pages'],1)
    def test_false_positive_and_miss_penalize_detection_not_fake_order(self):
        self.ref['pages'][0]['utterances'].append({'label':'Missing','points':[[.5,.8]]})
        self.doc['result']['bubbles'].append(dict(id='b3',order=3,type='text',x=.7,y=.7,w=.1,h=.1))
        result=self.score()['overall']
        self.assertAlmostEqual(result['detection_f1'],2/3)
        self.assertEqual(result['order_pairs'],1);self.assertEqual(result['order_agreement'],1)
        self.assertEqual(result['contours_unreviewed'],0) # false positives already penalized by F1
    def test_geometry_change_invalidates_visual_acceptance_even_with_same_id(self):
        before=self.score();self.doc['result']['bubbles'][0]['w']=.21
        after=self.score();self.assertEqual(after['overall']['contours_unreviewed'],1)
        self.assertIsNone(after['overall']['combined_estimate'])
        self.assertFalse(compare_metrics(before,after)['passed'])
    def test_order_id_or_confidence_change_does_not_invalidate_identical_geometry(self):
        a,b=self.doc['result']['bubbles']
        self.doc['result']['bubbles']=[dict(b,id='b1',order=1,confidence=.99),dict(a,id='b2',order=2)]
        result=self.score()['overall'];self.assertEqual(result['contours_unreviewed'],0)
        self.assertEqual(result['order_agreement'],0);self.assertEqual(result['combined_estimate'],0)
    def test_direction_and_invalid_metadata_reject_order_pairs(self):
        self.doc['result']['direction']='rtl';self.assertEqual(self.score()['overall']['order_agreement'],0)
        self.doc['result']['direction']='ltr';self.doc['result']['bubbles'][1]['order']=1
        self.assertEqual(self.score()['overall']['order_agreement'],0)
    def test_split_connected_balloon_is_not_two_correct_stops(self):
        self.ref['pages'][0]['utterances']=[{'label':'Joined','points':[[.2,.2],[.7,.2]]}]
        result=self.score()['overall'];self.assertEqual(result['true_positives'],0)
        self.assertEqual(result['false_positives'],2);self.assertEqual(result['false_negatives'],1)
    def test_unexpected_page_or_changed_image_rejected(self):
        self.score();(self.folder/'unexpected.json').write_text('{}',encoding='utf8')
        with self.assertRaises(ValueError):self.score()
        (self.folder/'unexpected.json').unlink();self.contours['pages'][0]['size']=[101,100]
        with self.assertRaises(ValueError):self.score()
    def test_rejected_and_excluded_contours_lower_score(self):
        self.contours['pages'][0]['regions'][0]['accepted']=False
        result=self.score()['overall'];self.assertEqual(result['contour_acceptance'],.5)
        self.ref['pages'][0]['utterances'][1]['exclude_points']=[[.7,.2]]
        self.assertEqual(self.score()['overall']['contour_acceptance'],0)

    def test_duplicate_reference_cannot_double_count_a_page(self):
        self.ref['pages'].append(copy.deepcopy(self.ref['pages'][0]))
        with self.assertRaises(ValueError):self.score()

    def test_non_boolean_visual_verdict_is_rejected(self):
        self.contours['pages'][0]['regions'][0]['accepted']='yes'
        with self.assertRaises(ValueError):self.score()


class ContentRemovalGateTests(unittest.TestCase):
    def setUp(self):
        self.old={'result':{'width':100,'height':100,'panels':[],'confidence':.9,
            'bubbles':[dict(id='b1',order=1,confidence=.9,x=.1),dict(id='b2',order=2,confidence=.9,x=.7)]},
            'analysis':{'reading_anchors':{'b1':[1,2],'b2':[3,4]},'text_check':{'regions':[{'region_id':'b1','ocr':['A']},{'region_id':'b2','ocr':['B']}]}},
            'review':{'verified':False,'flags':['b1 flag','b2 flag']}}
        self.rule={'sha_prefix':'image','kind':'event-ad','removed_region_ids':['b1'],'reason':'reviewed'}
        self.new=copy.deepcopy(self.old);self.new['result']['bubbles']=[dict(self.old['result']['bubbles'][1],id='b1',order=1)]
        self.new['analysis']['reading_anchors']={'b1':[3,4]}
        self.new['analysis']['text_check']['regions']=[{'region_id':'b1','ocr':['B']}]
        self.new['analysis']['content_filter']={'status':'applied','kind':'event-ad','removed_region_ids':['b1'],
           'preserved_id_mapping':{'b2':'b1'},'evidence':{'human':'reviewed'},
           'original':{'result':copy.deepcopy(self.old['result']),'reading_anchors':copy.deepcopy(self.old['analysis']['reading_anchors']),
              'text_check':copy.deepcopy(self.old['analysis']['text_check']),'review':copy.deepcopy(self.old['review'])}}
    def test_only_reviewed_removal_passes(self):
        self.assertEqual(compare_content_removals(self.old,self.new,self.rule),[])
        self.new['result']['bubbles']=[]
        self.assertTrue(compare_content_removals(self.old,self.new,self.rule))
    def test_modified_snapshot_cannot_self_authorize_loss(self):
        self.new['analysis']['content_filter']['original']['result']['bubbles'][0]['x']=.4
        self.assertTrue(compare_content_removals(self.old,self.new,self.rule))
    def test_remaining_geometry_ocr_and_anchor_are_protected(self):
        for field in ('geometry','ocr','anchor'):
            with self.subTest(field=field):
                doc=copy.deepcopy(self.new)
                if field=='geometry':doc['result']['bubbles'][0]['x']=.71
                elif field=='ocr':doc['analysis']['text_check']['regions'][0]['ocr']=[]
                else:doc['analysis']['reading_anchors']={}
                self.assertTrue(compare_content_removals(self.old,doc,self.rule))
    def test_missing_policy_page_blocks_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a';b=Path(temp)/'b';a.mkdir();b.mkdir()
            old=copy.deepcopy(self.old);old['lab']={'sha256':'other'}
            for folder in (a,b):(folder/'000-other.json').write_text(json.dumps(old),encoding='utf8')
            result=compare(a,b,{'content_removals':[self.rule]})
            self.assertFalse(result['passed']);self.assertIn('Missing reviewed',result['errors'][-1])
