import copy
import unittest
import cv2
import numpy as np
from PIL import Image
from tools.bubble_studio.geometry import contour_box
from tools.bubble_studio.tail_guard import screened_tail_guard
from tools.bubble_studio.regression_gate import contour_extension


class TailGuardTests(unittest.TestCase):
    def scene(self,complete=False,color=(255,255,255),open_border=False):
        width,height=440,280
        true=np.zeros((height,width),np.uint8)
        cv2.ellipse(true,(285,120),(100,65),0,0,360,255,-1)
        cv2.fillPoly(true,[np.array([[210,120],[85,208],[242,160]])],255)
        pixels=np.indices((height,width)).sum(axis=0)%2*160+40
        rgb=np.repeat(pixels[:,:,None],3,axis=2).astype(np.uint8)
        rgb[true>0]=color
        cv2.drawContours(rgb,cv2.findContours(true,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],-1,(0,0,0),1)
        # Recognisable ink contrast is required by the shared mask validator.
        for x in (254,272,290,308):cv2.rectangle(rgb,(x,110),(x+5,125),(0,0,0),-1)
        old=true.copy()
        if not complete:old[:,:180]=0
        b=contour_box(old,(0,0),width,height,.93)
        texts=[dict(box=[245,100,325,140],score=.95,label=1)]
        if open_border:rgb[0:121,260:275]=255
        return Image.fromarray(rgb),b,texts

    def test_long_extension_is_recovered_without_mutating_original(self):
        image,b,texts=self.scene()
        before=copy.deepcopy(b)
        result,audit=screened_tail_guard(image,b,texts)
        self.assertIsNotNone(audit)
        self.assertLess(result['x'],b['x'])
        self.assertEqual(audit['original_mask_preserved'],1)
        self.assertEqual(b,before)
        self.assertIsNone(contour_extension(b,result,*image.size,{'min_mask_growth':.03,'max_mask_growth':.20}))

    def test_complete_tail_is_unchanged(self):
        image,b,texts=self.scene(complete=True)
        result,audit=screened_tail_guard(image,b,texts)
        self.assertIs(result,b);self.assertIsNone(audit)

    def test_free_text_and_weak_text_are_never_extended(self):
        image,b,texts=self.scene()
        for label,score in [(2,.99),(1,.69)]:
            result,audit=screened_tail_guard(image,b,[dict(texts[0],label=label,score=score)])
            self.assertIs(result,b);self.assertIsNone(audit)

    def test_fill_escaping_to_page_is_rejected(self):
        image,b,texts=self.scene(open_border=True)
        result,audit=screened_tail_guard(image,b,texts)
        self.assertIs(result,b);self.assertIsNone(audit)

    def test_coloured_tail_uses_local_paper_colour(self):
        image,b,texts=self.scene(color=(190,220,245))
        result,audit=screened_tail_guard(image,b,texts)
        self.assertIsNotNone(audit)
        self.assertLess(result['x'],b['x'])

    def test_regression_gate_rejects_body_loss_and_oversized_growth(self):
        image,b,texts=self.scene()
        result,audit=screened_tail_guard(image,b,texts)
        self.assertIsNotNone(audit)
        shifted=copy.deepcopy(result);shifted['x']+=.08
        self.assertIsNotNone(contour_extension(b,shifted,*image.size,{}))
        self.assertIsNotNone(contour_extension(b,result,*image.size,{'max_mask_growth':.01}))

    def test_regression_gate_rejects_invalid_contour(self):
        image,b,_=self.scene()
        for value in (float('nan'),-1,2):
            bad=copy.deepcopy(b);bad['polygons'][0][0]['x']=value
            self.assertIsNotNone(contour_extension(b,bad,*image.size,{}))


if __name__=='__main__':unittest.main()
