import copy
from types import SimpleNamespace
import pytest
from tools.bubble_studio import page_finish


def test_failed_optional_stage_rolls_back_partial_changes_but_keeps_prior_success(monkeypatch):
    original=dict(result=dict(bubbles=[dict(id='b1')]),analysis={},review=dict(flags=[],verified=False))
    document=copy.deepcopy(original)
    def successful(image,doc,*args):
        doc['analysis']['first_stage']='kept'
        return doc
    def failing(image,doc,*args):
        doc['result']['bubbles'].clear()
        raise RuntimeError('Model unavailable')
    monkeypatch.setattr(page_finish,'refine_strips',successful)
    monkeypatch.setattr(page_finish,'refine_publishing',failing)
    actual=page_finish.refine_semantic_page(None,document,None,SimpleNamespace(strict=False))
    assert actual['result']==original['result']
    assert actual['analysis']['first_stage']=='kept'
    assert actual['analysis']['final_context_failures']==[dict(stage='failing',error='RuntimeError')]
    assert len(actual['review']['flags'])==1


def test_strict_quality_run_cannot_hide_an_optional_stage_failure(monkeypatch):
    def failing(*args):raise RuntimeError('Quality audit must fail')
    monkeypatch.setattr(page_finish,'refine_strips',failing)
    with pytest.raises(RuntimeError,match='Quality audit must fail'):
        page_finish.refine_semantic_page(None,dict(result={},analysis={},review={}),None,SimpleNamespace(strict=True))


def test_verified_page_never_enters_optional_stages(monkeypatch):
    def forbidden(*args):raise AssertionError('Verified page was modified')
    monkeypatch.setattr(page_finish,'refine_strips',forbidden)
    monkeypatch.setattr(page_finish,'refine_publishing',forbidden)
    document=dict(result={},analysis={},review=dict(verified=True))
    assert page_finish.refine_semantic_page(None,document,None,None) is document
