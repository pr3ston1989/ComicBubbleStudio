import copy
import pytest
from tools.bubble_studio.content_filter import apply_content_filter,restore_content_filter
from tools.bubble_studio.geometry import rectangle

SIZE=(1000,1500)
def row(text,box,score=.98):return dict(text=text,box=box,score=score)
def document():
    bubbles=[dict(rectangle([50,100,220,240],*SIZE,.9,'text',margin=0),id='b1',order=1,panel_id=None)]
    return {'result':dict(width=1000,height=1500,direction='ltr',panels=[],bubbles=bubbles,confidence=.9),
            'review':dict(verified=False,flags=['Check region b1']),
            'analysis':{'reading_anchors':{'b1':{k:bubbles[0][k] for k in ['x','y','w','h']}},'text_check':{'mode':'review','regions':[]}}}
def ad_rows():
    return [row('A CROSSOVER EVENT IS HERE!',[100,200,900,240]),
            row('READ NOW',[600,1250,800,1280]),row('FOR FREE',[590,1290,820,1320]),
            *[row(f'WEEK {i+1}',[80,850+i*100,180,875+i*100]) for i in range(3)],
            *[row(f'EPISODE {i+1} - 10/{i+1:02}/26',[200,850+i*80,500,880+i*80]) for i in range(4)]]

def test_confirmed_event_ad_is_reversible_and_keeps_full_original_evidence():
    d=document();before=copy.deepcopy(d);apply_content_filter(d,ad_rows())
    assert d['result']['bubbles']==[] and d['analysis']['reading_anchors']=={}
    assert d['analysis']['content_filter']['original']['result']==before['result']
    assert restore_content_filter(d)
    assert d['result']==before['result'] and d['review']==before['review']
    assert not restore_content_filter(d)

@pytest.mark.parametrize('case',['story-panel','no-header','no-dates','few-dates','no-weeks','no-cta','misaligned-cta','footer-only','weak'])
def test_marketing_footer_or_incomplete_evidence_never_deletes_story(case):
    d=document();rows=ad_rows()
    if case=='story-panel':d['result']['panels']=[rectangle([0,0,1000,700],*SIZE,.95,margin=0)]
    if case=='no-header':rows=rows[1:]
    if case=='no-dates':rows=rows[:-4]
    if case=='few-dates':rows=rows[:-1]
    if case=='no-weeks':rows=[r for r in rows if not r['text'].startswith('WEEK')]
    if case=='no-cta':rows=[r for r in rows if r['text']!='READ NOW']
    if case=='misaligned-cta':rows[2]['box']=[10,1290,200,1320]
    if case=='footer-only':rows[0]['box']=[100,1200,900,1240]
    if case=='weak':rows[0]['score']=.89
    before=copy.deepcopy(d['result']);apply_content_filter(d,rows)
    assert d['result']==before

def credits():
    d=document();rows=[row('Translation: Jane Smith',[300,400,500,418]),row('Lettering: Adam Jones',[550,400,750,418])]
    d['result']['panels']=[rectangle([0,0,1000,380],*SIZE,.95,margin=0),rectangle([0,440,1000,1400],*SIZE,.95,margin=0)]
    for i,r in enumerate(rows,2):
        b=dict(rectangle(r['box'],*SIZE,.9,'text',margin=6),id=f'b{i}',order=i,panel_id=None)
        d['result']['bubbles'].append(b)
        d['analysis']['reading_anchors'][b['id']]={k:b[k] for k in ['x','y','w','h']}
        d['analysis']['text_check']['regions'].append(dict(region_id=b['id'],box=r['box'],ocr=[dict(text=r['text'],score=.98,box=[0,0,1,1])]))
    return d,rows

def test_paired_credit_band_preserves_every_story_region_and_supports_undo():
    d,rows=credits();before=copy.deepcopy(d);apply_content_filter(d,rows)
    assert d['result']['bubbles']==before['result']['bubbles'][:1]
    assert d['analysis']['content_filter']['removed_region_ids']==['b2','b3']
    assert restore_content_filter(d) and d['result']==before['result']

@pytest.mark.parametrize('case',['single-label','no-colon','inside-panel','uncertain','contour','oversized','ordinary-speech','different-name'])
def test_ambiguous_credits_never_authorize_deleting_story(case):
    d,rows=credits()
    if case=='single-label':rows=rows[:1]
    if case=='no-colon':
        for r in rows:r['text']=r['text'].replace(':','')
    if case=='inside-panel':d['result']['panels']=[rectangle([0,0,1000,1000],*SIZE,.95,margin=0)]
    if case=='uncertain':
        for r in rows:r['score']=.89
    if case=='contour':
        for b in d['result']['bubbles'][1:]:b['polygons']=[[dict(x=0,y=0),dict(x=1,y=0),dict(x=1,y=1)]]
    if case=='oversized':
        for b in d['result']['bubbles'][1:]:b.update(y=0,h=.7)
    if case=='ordinary-speech':
        for check in d['analysis']['text_check']['regions']:check['ocr'][0]['text']='What does this translation mean?'
    if case=='different-name':
        for check in d['analysis']['text_check']['regions']:check['ocr'][0]['text']='Translation: Somebody Else'
    before=copy.deepcopy(d['result']);apply_content_filter(d,rows);assert d['result']==before

def test_repeated_cover_titles_only_flag_review_even_without_panels():
    d=document();rows=[row('COMIC TITLE',[x*200,y*250,x*200+110,y*250+18]) for x in range(4) for y in range(5)]
    before=copy.deepcopy(d['result']);apply_content_filter(d,rows)
    assert d['result']==before and d['analysis']['content_filter']['status']=='review-only'

def test_editor_restore_is_undoable_and_redoable():
    from tools.bubble_studio.review import Reviewer
    d,rows=credits();before=copy.deepcopy(d);apply_content_filter(d,rows);filtered=copy.deepcopy(d)
    editor=Reviewer.__new__(Reviewer);editor.index=0;editor.documents=[d]
    editor.undo_stack=[];editor.redo_stack=[];editor.load_page=lambda:None
    editor.restore_filtered();assert editor.documents[0]['result']==before['result']
    editor.undo();assert editor.documents[0]==filtered
    editor.redo();assert editor.documents[0]['result']==before['result']
