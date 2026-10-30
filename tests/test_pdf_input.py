import json
import hashlib
from pathlib import Path
import pytest
from PIL import Image
from tools.bubble_studio.pdf_input import import_pdf
from web.backend.comic_archive import list_image_entries,read_entry

FIXTURE=Path(__file__).resolve().parent/'fixtures/pdf-input-mixed.pdf'


def test_pdf_import_preserves_original_and_is_identical_with_optional_text_enabled(tmp_path):
    original=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    archive,meta,layers=import_pdf(FIXTURE,tmp_path/'a',False)
    assert layers is None and len(list_image_entries(archive))==4
    second,meta2,layers=import_pdf(FIXTURE,tmp_path/'b',True)
    assert archive.read_bytes()==second.read_bytes()
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==original
    assert 'Zażółć gęślą jaźń' in [r['text'] for r in layers[0]['rows']]
    assert not layers[1]['rows'] and not layers[1]['error']
    assert [r['text'] for r in layers[2]['rows']]==['NATIVE MIXED']
    assert [r['text'] for r in layers[3]['rows']]==['ROTATED CROP']


def test_native_text_coordinates_follow_rotated_cropped_render(tmp_path):
    archive,meta,layers=import_pdf(FIXTURE,tmp_path,True)
    import io,numpy as np
    from PIL import Image
    for index,(name,_) in enumerate(list_image_entries(archive)):
        with Image.open(io.BytesIO(read_entry(archive,name))) as im:gray=np.asarray(im.convert('L'))
        for row in layers[index]['rows']:
            a,b,c,d=map(int,row['box']);assert 0<=a<c<=gray.shape[1] and 0<=b<d<=gray.shape[0]
            assert (gray[b:d,a:c]<140).mean()>.05


def test_pdf_import_recovers_a_corrupt_page_checkpoint(tmp_path):
    archive,meta,_=import_pdf(FIXTURE,tmp_path,False)
    expected=archive.read_bytes();folder=archive.parent
    archive.unlink();(folder/'page-00002.png').write_bytes(b'broken')
    actual,_,_=import_pdf(FIXTURE,tmp_path,False)
    assert actual.read_bytes()==expected


def test_invalid_pdf_gives_readable_error_without_publishing(tmp_path):
    source=tmp_path/'broken.pdf';source.write_bytes(b'not PDF')
    with pytest.raises(ValueError,match='Nie można otworzyć PDF'):import_pdf(source,tmp_path/'work')
    assert not list((tmp_path/'work').rglob('*.cbz'))
