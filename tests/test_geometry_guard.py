import copy
import unittest
from PIL import Image
from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.quality_guard import guard_conflicts, region_guard

def polygon(box):
    b=rectangle(box,100,100,.9,margin=0)
    b['polygons']=[[dict(x=0,y=0),dict(x=1,y=0),dict(x=1,y=1),dict(x=0,y=1)]]
    b['_reading_box']=rectangle([box[0]+2,box[1]+2,box[2]-2,box[3]-2],100,100,.9,margin=0)
    return b

class OCR:
    def __init__(self,text):self.text=text
    def read(self,image): return [dict(text=self.text,score=.99)]

class GuardTests(unittest.TestCase):
    def test_crossing_masks_fall_back_without_losing_any_text_stop(self):
        b=[polygon([10,10,50,50]),polygon([30,30,70,70])]
        old=copy.deepcopy(b)
        audit=guard_conflicts(b,100,100)
        self.assertEqual(len(b),2)
        self.assertTrue(audit['pairs'])
        self.assertEqual(len(audit['original_contours']),2)
        self.assertTrue(all(x['type']=='text' and not x.get('polygons') for x in b))
        self.assertEqual(audit['original_contours'][0]['region']['polygons'],old[0]['polygons'])

    def test_disjoint_and_border_touching_masks_are_preserved(self):
        b=[polygon([10,10,40,40]),polygon([40,10,70,40])]
        before=copy.deepcopy(b)
        self.assertFalse(guard_conflicts(b,100,100)['pairs'])
        self.assertEqual(b,before)

    def test_whole_panel_text_does_not_become_a_huge_balloon(self):
        image=Image.new('RGB',(100,100),'black')
        b=polygon([10,10,90,90])
        text=[dict(box=[30,30,60,60])]
        result,audit=region_guard(image,b,text,[dict(box=[10,10,90,90])],OCR('How long has it been?'),'enclosed-color')
        self.assertEqual(result['type'],'text')
        self.assertEqual(audit['reason'],'panel-sized-text')

    def test_oversized_name_mask_is_kept_as_a_compact_text_region(self):
        b=polygon([10,10,90,90])
        result,audit=region_guard(Image.new('RGB',(100,100)),b,[dict(box=[30,30,60,60])],[],OCR('Zukon Mikaboshi'),'sam2')
        self.assertEqual(result['type'],'text')
        self.assertEqual(audit['reason'],'possible-name-label')

    def test_probable_effect_is_suppressed_only_after_contour_failure(self):
        image=Image.new('RGB',(100,100))
        text=[dict(box=[30,30,60,60])]
        self.assertIsNone(region_guard(image,rectangle([20,20,80,80],100,100,.9),text,[],OCR('POSE'),'text-fallback')[0])
        b=polygon([20,20,80,80])
        self.assertIs(region_guard(image,b,text,[],OCR('SNORT'),'enclosed-color')[0],b)

if __name__=='__main__':unittest.main()
