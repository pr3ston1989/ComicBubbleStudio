import copy
import pytest
from tools.bubble_studio.context_layout import layout,valid_plan,prose_groups


def row(text,box):return dict(text=text,box=box,score=.99)


def fields(x=100,y=100):
    return [row('REAL NAME: Example Person',[x,y,x+400,y+40]),
            row('HEIGHT: 180 cm',[x,y+100,x+180,y+140]),
            row('WEIGHT: 80 kg',[x,y+200,x+170,y+240])]


def test_independent_fields_cannot_be_merged_by_model_hints():
    rows=fields();old=copy.deepcopy(rows)
    groups=layout(rows,dict(groups=[dict(lines=[0,1,2])]),(1000,1000))
    assert len(groups)==3 and rows==old
    assert [g['field'] for g in groups]==['realname','height','weight']


def test_complete_column_extent_protects_words_omitted_from_a_short_ocr_fragment():
    groups=layout(fields(),None,(1000,1000))
    assert all(g['box'][2]==500 for g in groups)


@pytest.mark.parametrize('direction,first_x',[('ltr',100),('rtl',600)])
def test_side_by_side_profiles_are_read_as_whole_columns(direction,first_x):
    groups=layout(fields(100)+fields(600),None,(1200,1000),direction)
    assert [g['box'][0] for g in groups[:3]]==[first_x]*3


def test_upper_right_profile_precedes_lower_left_profile_in_ltr():
    groups=layout(fields(600,50)+fields(100,600),None,(1200,1200),'ltr')
    assert [g['box'][0] for g in groups[:3]]==[600]*3


@pytest.mark.parametrize('plan',[{'groups':[{'lines':[0,99]}]}, {'groups':[{'lines':[True]}]}, {'groups':[{'lines':[0,0]}]}])
def test_hallucinated_or_duplicate_ocr_ids_never_authorize_layout(plan):
    assert not valid_plan(plan,3)
    assert len(layout(fields(),plan,(1000,1000)))==3


def test_uncertain_or_out_of_page_ocr_cannot_replace_a_profile():
    for failure in ['uncertain','outside']:
        rows=fields()
        if failure=='uncertain':rows[0]['score']=.5
        else:rows[0]['box'][2]=1500
        assert not layout(rows,None,(1000,1000))


def test_recap_positive_group_cannot_smuggle_creator_credit_column():
    rows=[row('A story begins with the hero searching for a lost friend.',[50,100,450,130]),
          row('The journey takes them through a strange and distant land.',[50,140,450,170]),
          row('Finally they discover the truth and return safely home.',[50,180,450,210]),
          row('ARTIST: SOME CREATOR',[650,140,950,180])]
    result=prose_groups(rows,dict(groups=[dict(role='narration',lines=[0,1,2,3])]),(1000,1000))
    assert len(result)==1 and result[0]['box']==[50,100,450,210]
    assert len(result[0]['rows'])==3
