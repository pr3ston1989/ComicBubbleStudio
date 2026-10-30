import copy
import json
import tempfile
import unittest
from pathlib import Path
from tools.bubble_studio.regression_gate import compare

class RegressionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.root=Path(self.temp.name)
        self.a=self.root/'old';self.b=self.root/'new';self.a.mkdir();self.b.mkdir()
        self.region=dict(id='b1',order=1,panel_id=None,type='bubble',confidence=.9,source='external',x=.1,y=.1,w=.8,h=.8,
                         polygons=[[dict(x=0,y=0),dict(x=1,y=0),dict(x=1,y=1)]])
        self.doc={'lab':{'sha256':'image'},'result':{'width':100,'height':100,'direction':'rtl','panels':[],
                  'bubbles':[self.region]},'analysis':{'text_check':{'regions':[dict(region_id='b1',box=[10,10,90,90],
                  ocr=[dict(text='All words',score=.99,box=[.3,.3,.6,.6])])]}}}
        self.policy={'changes':[dict(sha_prefix='abcdef',region_id='b1',expected_type='text',
           allowed_fields=['x','y','w','h','type','polygons','polygon'],max_bbox_area_ratio=.65)]}
    def tearDown(self):self.temp.cleanup()
    def save(self,new):
        (self.a/'000-abcdef.json').write_text(json.dumps(self.doc),encoding='utf-8')
        (self.b/'000-abcdef.json').write_text(json.dumps(new),encoding='utf-8')
    def improved(self):
        new=copy.deepcopy(self.doc)
        b=new['result']['bubbles'][0]
        b.update(x=.3,y=.3,w=.35,h=.35,type='text');b.pop('polygons')
        return new
    def test_explicit_correction_preserves_words_and_identity(self):
        self.save(self.improved())
        self.assertTrue(compare(self.a,self.b,self.policy)['passed'])
    def test_any_unapproved_region_change_blocks_promotion(self):
        self.save(self.improved())
        self.assertFalse(compare(self.a,self.b,{'changes':[]})['passed'])
    def test_changed_reading_order_or_panel_blocks_promotion(self):
        for field,value in [('order',2),('panel_id','p2'),('confidence',.8)]:
            new=self.improved();new['result']['bubbles'][0][field]=value;self.save(new)
            self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
    def test_clipping_a_word_blocks_promotion(self):
        new=self.improved();new['result']['bubbles'][0]['w']=.1;self.save(new)
        self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
    def test_different_page_identity_and_missing_pages_block_promotion(self):
        new=self.improved();new['lab']['sha256']='different';self.save(new)
        self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
        (self.b/'000-abcdef.json').unlink()
        self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
    def test_empty_baseline_never_passes(self):
        self.assertFalse(compare(self.a,self.b,{'changes':[]})['passed'])
    def test_absent_identity_or_word_evidence_blocks_promotion(self):
        new=self.improved();self.save(new)
        doc=copy.deepcopy(self.doc);doc.pop('lab')
        (self.a/'000-abcdef.json').write_text(json.dumps(doc),encoding='utf-8')
        self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
        self.doc['analysis']['text_check']['regions']=[]
        self.save(new)
        self.assertFalse(compare(self.a,self.b,self.policy)['passed'])
    def test_unchanged_control_pages_pass_without_exceptions(self):
        self.save(self.doc)
        self.assertTrue(compare(self.a,self.b,{'changes':[]})['passed'])

    def reading_swap(self):
        self.doc['result']['bubbles'].append(dict(self.region,id='b2',order=2,x=.2,w=.4))
        new=copy.deepcopy(self.doc)
        new['result']['bubbles']=[dict(new['result']['bubbles'][1],id='b1',order=1),dict(new['result']['bubbles'][0],id='b2',order=2)]
        policy={'reading_order_changes':[dict(sha_prefix='abcdef',old_region_sequence=['b2','b1'],reason='Reviewed order')],'changes':[]}
        return new,policy

    def test_reviewed_reading_permutation_keeps_exact_geometry(self):
        new,policy=self.reading_swap();self.save(new)
        result=compare(self.a,self.b,policy)
        self.assertTrue(result['passed']);self.assertEqual(len(result['approved_order_changes']),1)

    def test_reviewed_order_never_authorizes_a_geometry_change(self):
        new,policy=self.reading_swap();new['result']['bubbles'][0]['x']+=.01;self.save(new)
        self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def test_wrong_order_permutation_is_rejected(self):
        new,policy=self.reading_swap();policy['reading_order_changes'][0]['old_region_sequence']=['b1','b2'];self.save(new)
        self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def test_policy_cannot_silently_skip_a_missing_order_page(self):
        self.save(self.doc)
        policy={'reading_order_changes':[dict(sha_prefix='missing',old_region_sequence=['b1'],reason='Missing page')]}
        self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def split_case(self):
        parent=dict(id='b1',order=1,panel_id=None,type='text',confidence=.9,source='external',x=.1,y=.1,w=.8,h=.2)
        protected=dict(parent,id='b2',order=2,x=.2,y=.6,w=.2,h=.1)
        self.doc['result']['bubbles']=[parent,protected]
        self.doc['analysis']['text_check']['regions']=[dict(region_id='b1',box=[10,10,90,30],ocr=[
            dict(box=[x,y,x+.2,y+.2],text='Every word stays',score=.98)
            for x in (.01,.7) for y in (.1,.6)])]
        new=copy.deepcopy(self.doc)
        replacements=[dict(parent,id='b1',order=1,x=.1,w=.2),dict(parent,id='b2',order=2,x=.65,w=.2)]
        new['result']['bubbles']=copy.deepcopy(replacements)+[dict(protected,id='b3',order=3)]
        policy={'text_split_changes':[dict(sha_prefix='abcdef',reason='Reviewed columns',preserved_regions={'b2':'b3'},
                splits=[dict(old_region='b1',new_regions=replacements)])]}
        return new,policy

    def test_reviewed_split_protects_every_baseline_ocr_line(self):
        new,policy=self.split_case();self.save(new)
        result=compare(self.a,self.b,policy)
        self.assertTrue(result['passed'],result['errors'])
        self.assertEqual(len(result['approved_text_splits']),1)

    def test_self_reported_split_never_bypasses_review_or_clipping_check(self):
        new,policy=self.split_case()
        new['analysis']['text_splits']=[dict(passed=True)]
        self.save(new);self.assertFalse(compare(self.a,self.b,{})['passed'])
        new['result']['bubbles'][0]['w']=.05
        # Even updating the reviewed coordinates cannot authorize cropping a line.
        policy['text_split_changes'][0]['splits'][0]['new_regions'][0]['w']=.05
        self.save(new);self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def test_split_cannot_authorize_other_geometry_or_panel_changes(self):
        for field,value in [('x',.25),('panel_id','p2'),('confidence',.7)]:
            new,policy=self.split_case();new['result']['bubbles'][-1][field]=value
            self.save(new);self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def test_split_requires_complete_nonduplicate_mapping_and_existing_page(self):
        for failure in ('missing-object','duplicate-object','absent-page'):
            new,policy=self.split_case();rule=policy['text_split_changes'][0]
            if failure=='missing-object':rule['preserved_regions']={}
            if failure=='duplicate-object':rule['preserved_regions']['b2']='b2'
            if failure=='absent-page':rule['sha_prefix']='missing'
            self.save(new);self.assertFalse(compare(self.a,self.b,policy)['passed'])

    def test_split_does_not_accept_contours_or_uncertain_baseline_letters(self):
        for failure in ('contour','uncertain','missing-ocr'):
            new,policy=self.split_case()
            if failure=='contour':self.doc['result']['bubbles'][0]['polygons']=self.region['polygons']
            if failure=='uncertain':self.doc['analysis']['text_check']['regions'][0]['ocr'][0]['score']=.6
            if failure=='missing-ocr':self.doc['analysis']['text_check']['regions']=[]
            self.save(new);self.assertFalse(compare(self.a,self.b,policy)['passed'])

if __name__=='__main__':unittest.main()
