import copy,hashlib,io,json
from pathlib import Path
import numpy as np
from PIL import Image
from tools.bubble_studio.text_export import extract_page,write_exports,_merge_native,_covered,_ordered_lines
from tools.bubble_studio.geometry import rectangle,ordered_result
from tools.bubble_studio.runner import process_comic,optional_export
from tools.bubble_studio.pdf_input import import_pdf
from web.backend.comic_bubble_package import package_path,load_package


class FakeOCR:
    def read(self,image):return [dict(text='hello',score=.98,box=[.2,.3,.8,.6])]
    def locate_context(self,image):return [dict(text='EXTRA',score=.99,box=[0,0,10,10])]


def test_export_obeys_saved_reading_order_and_does_not_mutate_geometry():
    bubbles=[dict(rectangle([300,20,480,150],500,200,.9,margin=0),id='b1',order=1),dict(rectangle([20,20,200,150],500,200,.9,margin=0),id='b2',order=2)]
    doc=dict(result=dict(direction='rtl',bubbles=bubbles));old=copy.deepcopy(doc)
    result=extract_page(Image.new('RGB',(500,200),'white'),doc,FakeOCR(),all_text=True)
    assert [r['id'] for r in result['regions']]==['b1','b2'] and len(result['extra'])==1
    assert doc==old


def test_mixed_pdf_keeps_ocr_only_words_and_replaces_matching_native_text():
    ocr=[dict(text='HELLO',box=[0,0,100,30],score=.9,source='ocr'),dict(text='SCAN',box=[200,0,300,30],score=.9,source='ocr')]
    native=[dict(text='Hello',box=[0,0,100,30],score=1,source='pdf-text')]
    rows=_merge_native(ocr,native)
    assert [r['text'] for r in rows]==['SCAN','Hello']
    partial=_merge_native([dict(text='HELLO SCANNED',box=[0,0,200,30],score=.9,source='ocr')],native)
    assert any(r['text']=='HELLO SCANNED' and r['merge_uncertain'] for r in partial)
    wrong=_merge_native([dict(text='WRONG OCR',box=[0,0,100,30],score=.6,source='ocr')],native)
    assert [r['text'] for r in wrong]==['Hello']
    accented=_merge_native([dict(text='Zazolc gesla jazn',box=[164,95,556,155],score=.96,source='ocr')],
                          [dict(text='Zażółć gęślą jaźń',box=[168,103,549,149],score=1,source='pdf-text')])
    assert [r['text'] for r in accented]==['Zażółć gęślą jaźń']
    fragments=_merge_native([dict(text='Zazo',box=[156,90,327,153],score=.9,source='ocr'),dict(text='gesla jazn',box=[309,87,567,165],score=.9,source='ocr')],
                          [dict(text='Zażółć gęślą jaźń',box=[168,103,549,149],score=1,source='pdf-text')])
    assert [r['text'] for r in fragments]==['Zażółć gęślą jaźń']


def test_native_line_mostly_outside_crop_is_not_assigned_to_balloon():
    assert _covered(np.ones((100,100),np.uint8),[25,25,75,75])==1
    assert _covered(np.ones((100,100),np.uint8),[25,-200,75,75])<.3


def column_rows():
    return [dict(text=side+str(i),box=[x-25,y-8,x+25,y+8],score=.99,source='ocr') for i,y in enumerate([60,100,140]) for side,x in [('L',75),('R',225)]]


def test_connected_lobes_export_complete_text_columns_in_both_directions():
    import cv2
    mask=np.zeros((200,300),np.uint8)
    for x in [75,225]:cv2.ellipse(mask,(x,100),(70,90),0,0,360,1,-1)
    cv2.rectangle(mask,(135,70),(165,130),1,-1)
    for direction,expected in [('ltr',['L0','L1','L2','R0','R1','R2']),('rtl',['R0','R1','R2','L0','L1','L2'])]:
        assert [r['text'] for r in _ordered_lines(column_rows(),mask,(0,0),direction)]==expected


def test_ordinary_oval_word_columns_stay_in_line_order():
    import cv2
    mask=np.zeros((200,300),np.uint8);cv2.ellipse(mask,(150,100),(145,95),0,0,360,1,-1)
    for direction in ['ltr','rtl']:
        assert [r['text'] for r in _ordered_lines(column_rows(),mask,(0,0),direction)]==['L0','R0','L1','R1','L2','R2']


def test_empty_pages_filenames_html_escaping_and_uncertain_text_are_explicit(tmp_path):
    pages=[dict(page=1,filename='001.png',regions=[],extra=[]),dict(page=2,filename='002.png',regions=[dict(order=1,text='<script>żółć</script>',uncertain=True)],extra=[])]
    paths=write_exports(tmp_path/'comic','<title>',pages,'html');assert len(paths)==3
    text=Path(paths[0]).read_text(encoding='utf-8-sig');html=Path(paths[1]).read_text(encoding='utf8')
    assert 'Strona 1 — 001.png' in text and 'Brak tekstu' in text and 'do sprawdzenia' in text
    assert '<script>' not in html and '&lt;script&gt;' in html


class FakeAnalyzer:
    provenance={};device_info={};quality='precise';calls=0
    def analyze(self,image,**kwargs):
        self.calls+=1;w,h=image.size
        bs=[rectangle([w*.05,h*.18,w*.45,h*.42],w,h,.95,margin=0),rectangle([w*.55,h*.18,w*.95,h*.42],w,h,.95,margin=0)]
        return dict(result=ordered_result([],bs,w,h,kwargs['direction'],'auto'),analysis={},review=dict(flags=[],verified=False))


def test_enabling_export_on_ready_package_changes_neither_bytes_nor_analysis(tmp_path,monkeypatch):
    fixture=Path(__file__).parent/'fixtures/pdf-input-mixed.pdf';source,meta,layers=import_pdf(fixture,tmp_path/'pdf',True)
    model=FakeAnalyzer();out=tmp_path/'out';work=tmp_path/'work';relative=Path('comic.cbz')
    first=process_comic(source,relative,out,work,model);comic=out/relative;sidecar=package_path(comic);before=sidecar.read_bytes();calls=model.calls
    import tools.bubble_studio.text_export as module
    original=module.export_comic
    monkeypatch.setattr(module,'export_comic',lambda source,format,all_text,**kwargs:original(source,format,all_text,checker=FakeOCR(),**kwargs))
    second=process_comic(source,relative,out,work,model,text_export='html',native_layers=layers)
    assert second['status']=='skipped' and sidecar.read_bytes()==before and model.calls==calls
    assert len(second['text_exports'])==3 and load_package(comic)


def test_optional_export_failure_preserves_completed_package_status(monkeypatch):
    import tools.bubble_studio.text_export as module
    def broken(*args,**kwargs):raise RuntimeError('disk full')
    monkeypatch.setattr(module,'export_comic',broken)
    outcome=optional_export(dict(status='ready'),Path('comic.cbz'),'html')
    assert outcome['status']=='ready' and outcome['text_export_error']=='disk full'


def test_export_off_does_not_call_ocr_or_exporter(monkeypatch):
    import tools.bubble_studio.text_export as module
    def forbidden(*args,**kwargs):raise AssertionError('Optional feature was enabled')
    monkeypatch.setattr(module,'export_comic',forbidden)
    outcome=dict(status='ready');assert optional_export(outcome,Path('comic.cbz'),'off') is outcome


def test_export_only_cli_never_imports_bubble_models(tmp_path,monkeypatch):
    import builtins
    from tools.bubble_studio.runner import main
    import tools.bubble_studio.text_export as module
    source,_,_=import_pdf(Path(__file__).parent/'fixtures/pdf-input-mixed.pdf',tmp_path/'pdf')
    analyzer=FakeAnalyzer();process_comic(source,Path('comic.cbz'),tmp_path/'out',tmp_path/'work',analyzer)
    comic=tmp_path/'out/comic.cbz';before=package_path(comic).read_bytes();calls=analyzer.calls
    original=module.export_comic
    monkeypatch.setattr(module,'export_comic',lambda source,format,all_text,**kwargs:original(source,format,all_text,checker=FakeOCR(),**kwargs))
    importer=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name=='models' or name=='tools.bubble_studio.models':raise AssertionError('Export-only loaded bubble models')
        return importer(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    assert main(['--input',str(comic),'--export-only','--text-export','txt'])==0
    assert package_path(comic).read_bytes()==before and analyzer.calls==calls
    assert Path(str(comic)+'.tekst.txt').is_file()


def test_pdf_queue_publishes_reader_compatible_cbz_and_separate_export(tmp_path,monkeypatch):
    import sys,types
    import tools.bubble_studio.runner as runner
    import tools.bubble_studio.text_export as module
    source=tmp_path/'input/Komiksy/próba.pdf';source.parent.mkdir(parents=True)
    source.write_bytes((Path(__file__).parent/'fixtures/pdf-input-mixed.pdf').read_bytes());before=source.read_bytes()
    monkeypatch.setattr(runner,'STUDIO',tmp_path/'studio')
    monkeypatch.setitem(sys.modules,'tools.bubble_studio.models',types.SimpleNamespace(GPUModels=lambda **kwargs:FakeAnalyzer()))
    original=module.export_comic
    monkeypatch.setattr(module,'export_comic',lambda source,format,all_text,**kwargs:original(source,format,all_text,checker=FakeOCR(),**kwargs))
    output=tmp_path/'output'
    assert runner.main(['--input',str(tmp_path/'input'),'--output',str(output),'--work',str(tmp_path/'work'),'--text-export','html'])==0
    comic=output/'Komiksy/próba (PDF).cbz';package=load_package(comic)
    assert package and len(package.manifest['pages'])==4 and source.read_bytes()==before
    assert package.manifest['config']['pipeline']==runner.PIPELINE_VERSION
    assert Path(str(comic)+'.tekst.html').is_file()
    summary=(output/'.nokturn-bubble-review/index.html').read_text(encoding='utf8')
    assert 'Tekst HTML' in summary and 'Tekst TXT' in summary
