"""Text-column recovery protects contours, uncertain letters and single passages."""
import copy
import pytest
from PIL import Image
from tools.bubble_studio.geometry import rectangle, ordered_result
from tools.bubble_studio.textcheck import TextCheck, split_text_columns


class OCR:
    latin_dialogue = staticmethod(TextCheck.latin_dialogue)
    def __init__(self,rows): self.rows=rows
    def read(self,image): return self.rows


def lines():
    return [{'box':[x,y,x+.3,y+.15],'score':.97,'text':text}
            for x,words in [(0.03,['I cannot see','anything here.']),(.65,['Where have','you gone?'])]
            for y,text in zip([.15,.55],words)]


@pytest.mark.parametrize('scale,offset',[(1,0),(2,0),(1,100)])
def test_independent_columns_preserve_every_row_and_reading_direction(scale,offset):
    image=Image.new('RGB',(1000*scale,800*scale),'black')
    original=rectangle([offset,100*scale,offset+800*scale,300*scale],*image.size,.91,'text',margin=0)
    frozen=copy.deepcopy(original);rows=lines()
    result,audit=split_text_columns(OCR(rows),image,[original])
    assert len(result)==2 and len(audit)==1 and original==frozen
    for row in rows:
        x1=offset+row['box'][0]*800*scale;x2=offset+row['box'][2]*800*scale
        y1=100*scale+row['box'][1]*200*scale;y2=100*scale+row['box'][3]*200*scale
        assert sum(b['x']*image.width<=x1 and (b['x']+b['w'])*image.width>=x2
                   and b['y']*image.height<=y1 and (b['y']+b['h'])*image.height>=y2 for b in result)==1
    for direction in ('ltr','rtl'):
        ordered=ordered_result([],copy.deepcopy(result),*image.size,direction,'auto')['bubbles']
        assert (ordered[0]['x']<ordered[1]['x'])==(direction=='ltr')


@pytest.mark.parametrize('case',['contour','uncertain','bridge','stacked','effect','single-line','bad-box'])
def test_ambiguous_or_contoured_regions_are_unchanged(case):
    image=Image.new('RGB',(1000,800),'white');rows=lines()
    bubble=rectangle([50,100,850,300],*image.size,.9,'text',margin=0)
    if case=='contour': bubble['polygons']=[[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1}]]
    if case=='uncertain': rows[0]['score']=.84
    if case=='bridge': rows.append(dict(box=[.3,.35,.8,.5],score=.99,text='This is one line.'))
    if case=='stacked':
        for r in rows[:2]: r['box'][1:4:2]=[.05,.2]
        for r in rows[2:]: r['box'][1:4:2]=[.7,.85]
    if case=='effect':
        for r in rows[:2]:r['text']='SLAM SLAM'
    if case=='single-line':rows=rows[:2]+rows[2:3]
    if case=='bad-box':rows[0]['box'][0]=float('nan')
    result,audit=split_text_columns(OCR(rows),image,[bubble])
    assert result==[bubble] and audit==[]
