"""Read-only PDF import to a deterministic CBZ accepted by Nokturn."""
from __future__ import annotations
import hashlib
import io
import json
import math
import zipfile
from contextlib import closing
from pathlib import Path
from web.backend.comic_bubble_package import file_sha256

RENDER_PROFILE = 'pdfium-5.14.0-200dpi-max3200-v1'
MAX_PAGES = 5000
MAX_TEXT_RECTS = 30000


def _atomic(path, data):
    temporary=path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(data,ensure_ascii=False,allow_nan=False),encoding='utf8')
    temporary.replace(path)


def _native_lines(page, bitmap):
    """Map PDF rectangles through the exact renderer transform (rotation/crop included)."""
    rows=[];converter=bitmap.get_posconv(page)
    with closing(page.get_textpage()) as text:
        count=text.count_rects()
        if count>MAX_TEXT_RECTS:raise ValueError('Zbyt wiele obszarów warstwy tekstowej PDF')
        for index in range(count):
            left,bottom,right,top=text.get_rect(index)
            value=text.get_text_bounded(left,bottom,right,top).replace('\r\n','\n').strip()
            if not value or '\ufffd' in value or any(ord(c)<32 and c not in '\n\t' for c in value):continue
            points=[converter.to_bitmap(x,y) for x,y in [(left,bottom),(left,top),(right,bottom),(right,top)]]
            xs,ys=zip(*points);box=[max(0,min(xs)),max(0,min(ys)),min(bitmap.width,max(xs)),min(bitmap.height,max(ys))]
            if box[2]<=box[0] or box[3]<=box[1]:continue
            if not any(r['text']==value and sum(abs(a-b) for a,b in zip(r['box'],box))<4 for r in rows):
                rows.append(dict(text=value,box=box,score=1.0,source='pdf-text'))
    return rows


def import_pdf(source: Path, work: Path, include_text=False, notify=None):
    """Return derived archive and optional text; never alter the source PDF."""
    import pypdfium2 as pdfium
    source=Path(source);checksum=file_sha256(source)
    key=hashlib.sha256((checksum+RENDER_PROFILE).encode()).hexdigest()[:24]
    folder=Path(work)/'pdf-import'/key;folder.mkdir(parents=True,exist_ok=True)
    archive=folder/(source.stem+' (PDF).cbz');manifest_path=folder/'conversion.json'
    conversion=None
    if manifest_path.is_file() and archive.is_file():
        try:
            candidate=json.loads(manifest_path.read_text(encoding='utf8'))
            if candidate['pdf_sha256']==checksum and candidate['render_profile']==RENDER_PROFILE and file_sha256(archive)==candidate['cbz_sha256']:
                conversion=candidate
        except (ValueError,KeyError,OSError):pass
    layers=[]
    try:
        pdf=pdfium.PdfDocument(source)
    except pdfium.PdfiumError as error:
        raise ValueError('Nie można otworzyć PDF. Sprawdź plik i usuń ochronę hasłem przed importem.') from error
    with pdf:
        if not 0<len(pdf)<=MAX_PAGES:raise ValueError('Nieprawidłowa lub zbyt duża liczba stron PDF')
        if conversion is None or include_text:
            for index in range(len(pdf)):
                if notify:notify(index+1,len(pdf))
                png=folder/f'page-{index+1:05}.png';stamp=folder/f'page-{index+1:05}.json'
                cached=False
                if png.is_file() and stamp.is_file():
                    try:
                        info=json.loads(stamp.read_text(encoding='utf8'));cached=info['sha256']==file_sha256(png) and info['render_profile']==RENDER_PROFILE
                    except (ValueError,KeyError,OSError):pass
                if cached and not include_text:continue
                with closing(pdf[index]) as page:
                    width,height=page.get_size()
                    if not all(math.isfinite(v) and v>0 for v in (width,height)):raise ValueError('Nieprawidłowy rozmiar strony PDF')
                    scale=min(200/72,3200/max(width,height))
                    with closing(page.render(scale=scale,rev_byteorder=True)) as bitmap:
                        if not cached:
                            image=bitmap.to_pil().convert('RGB');tmp=png.with_name(png.name+'.partial');image.save(tmp,format='PNG');tmp.replace(png)
                            _atomic(stamp,dict(sha256=file_sha256(png),render_profile=RENDER_PROFILE,width=image.width,height=image.height))
                        if include_text:
                            try:layers.append(dict(rows=_native_lines(page,bitmap),error=None))
                            except (ValueError,RuntimeError) as error:layers.append(dict(rows=[],error=type(error).__name__))
        if conversion is None:
            temporary=archive.with_name(archive.name+'.partial')
            with zipfile.ZipFile(temporary,'w',zipfile.ZIP_STORED) as output:
                for index in range(len(pdf)):
                    info=zipfile.ZipInfo(f'{index+1:05}.png',date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED
                    output.writestr(info,(folder/f'page-{index+1:05}.png').read_bytes())
            with zipfile.ZipFile(temporary) as check:
                if check.testzip() is not None:raise ValueError('Nieprawidłowy wynik konwersji PDF')
            if file_sha256(source)!=checksum:raise ValueError('PDF zmienił się podczas importu')
            temporary.replace(archive)
            conversion=dict(pdf_name=source.name,pdf_sha256=checksum,cbz_sha256=file_sha256(archive),pages=len(pdf),render_profile=RENDER_PROFILE)
            _atomic(manifest_path,conversion)
    if file_sha256(source)!=checksum:raise ValueError('PDF zmienił się podczas pracy')
    return archive,conversion,layers if include_text else None
