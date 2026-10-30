"""Conservative artwork rejection must not degrade real balloon styles."""
import copy
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from PIL import Image
from tools.bubble_studio.geometry import contour_box
from tools.bubble_studio.quality_guard import free_text_artwork_guard


class Reader:
    def __init__(self, rows):self.rows=rows
    def read(self,image):return self.rows


class FreeTextGuardTests(unittest.TestCase):
    def setUp(self):
        mask=np.zeros((300,300),np.uint8)
        points=np.array([[30,50],[200,50],[200,120],[270,120],[270,260],[200,260],[200,210],[30,210]])
        cv2.fillPoly(mask,[points],255)
        self.bubble=contour_box(mask,(0,0),300,300,.92)
        pixels=np.indices((300,300)).sum(axis=0)%2*120+40
        rgb=np.repeat(pixels[:,:,None],3,axis=2).astype(np.uint8)
        rgb[85:161,60:161]=255
        self.image=Image.fromarray(rgb)
        self.texts=[dict(label=2,score=.95,box=[60,85,160,160])]
        # contour_box includes the last mask pixel in its bounding dimensions.
        self.rows=[dict(text='I CAN HEAR YOU.',score=.99,box=[35/241,40/211,120/241,100/211])]

    def test_only_artwork_mask_becomes_text_and_original_is_recoverable(self):
        before=copy.deepcopy(self.bubble)
        result,audit=free_text_artwork_guard(self.image,self.bubble,self.texts,Reader(self.rows))
        self.assertEqual(result['type'],'text')
        self.assertFalse(result.get('polygons'))
        self.assertEqual(audit['ocr_lines_preserved'],1)
        self.assertEqual(audit['original_region'],before)
        self.assertEqual(self.bubble,before)

    def test_uniform_spiky_balloon_keeps_exact_original_geometry(self):
        image=Image.new('RGB',(300,300),'white')
        result,audit=free_text_artwork_guard(image,self.bubble,self.texts,Reader(self.rows))
        self.assertIs(result,self.bubble)
        self.assertIsNone(audit)

    def test_mostly_paper_artwork_still_requires_all_ocr_inside_text(self):
        rgb=np.full((300,300,3),255,np.uint8)
        rgb[:,::7]=40
        result,audit=free_text_artwork_guard(Image.fromarray(rgb),self.bubble,self.texts,Reader(self.rows))
        self.assertIsNotNone(audit)
        self.assertGreater(audit['background_agreement'],.80)
        self.assertLess(audit['background_agreement'],.90)
        self.assertEqual(result['type'],'text')

    def test_page_edge_branch_keeps_real_or_unconfirmed_boundaries(self):
        b=copy.deepcopy(self.bubble);b['x']=0
        texts=[dict(self.texts[0],box=[30,85,130,160])]
        for support in (.2,.99):
            with patch('tools.bubble_studio.refinement.boundary_support',return_value=support):
                result,audit=free_text_artwork_guard(Image.new('RGB',(300,300),'white'),b,texts,Reader(self.rows))
                self.assertIs(result,b);self.assertIsNone(audit)
        with patch('tools.bubble_studio.refinement.boundary_support',return_value=.82):
            result,audit=free_text_artwork_guard(Image.new('RGB',(300,300),'white'),b,texts,Reader(self.rows))
            self.assertEqual(result['type'],'text')
            self.assertEqual(audit['criterion'],'page-edge-background-without-supported-outline')

    def test_coloured_balloon_is_preserved_even_with_letter_colour_dominance(self):
        rgb=np.zeros((300,300,3),np.uint8);rgb[:]=[85,45,130]
        # More ink than paper inside tight OCR lines must not pick the ink colour.
        rgb[90:150,65:150]=[240,190,40]
        rgb[90:110,65:150]=[85,45,130]
        result,audit=free_text_artwork_guard(Image.fromarray(rgb),self.bubble,self.texts,Reader(self.rows))
        self.assertIs(result,self.bubble)
        self.assertIsNone(audit)

    def test_compact_transparent_balloon_is_preserved_on_a_complex_drawing(self):
        mask=np.zeros((300,300),np.uint8)
        cv2.ellipse(mask,(150,150),(100,130),0,0,360,255,-1)
        b=contour_box(mask,(0,0),300,300,.95)
        result,audit=free_text_artwork_guard(self.image,b,self.texts,Reader(self.rows))
        self.assertIs(result,b)
        self.assertIsNone(audit)

    def test_text_inside_balloon_or_weak_detector_never_triggers(self):
        for label,score in [(1,.99),(2,.84)]:
            texts=[dict(self.texts[0],label=label,score=score)]
            result,audit=free_text_artwork_guard(self.image,self.bubble,texts,Reader(self.rows))
            self.assertIs(result,self.bubble)
            self.assertIsNone(audit)

    def test_even_a_weak_ocr_line_outside_the_target_blocks_cropping(self):
        rows=self.rows+[dict(text='Maybe a small word',score=.52,box=[.7,.7,.9,.8])]
        result,audit=free_text_artwork_guard(self.image,self.bubble,self.texts,Reader(rows))
        self.assertIs(result,self.bubble)
        self.assertIsNone(audit)

    def test_missing_ocr_positions_and_unconfirmed_letters_do_not_trigger(self):
        for rows in [[dict(text='TEXT',score=.99)],[],[dict(self.rows[0],score=.7)]]:
            result,audit=free_text_artwork_guard(self.image,self.bubble,self.texts,Reader(rows))
            self.assertIs(result,self.bubble)
            self.assertIsNone(audit)


if __name__=='__main__':unittest.main()
