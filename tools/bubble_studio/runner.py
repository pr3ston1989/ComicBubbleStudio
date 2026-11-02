"""Resumable comic processing, atomic publication, and local visual review reports."""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import logging
import os
import shutil
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps
from web.backend.comic_archive import ARCHIVE_EXTENSIONS, IMAGE_EXTENSIONS, list_image_entries, read_entry
from web.backend.comic_bubble_package import BubblePackageError, file_sha256, source_sha256, package_path, is_bubble_package, read_manifest, validate_result
from .config import ENGINE_VERSION, series_settings
from .package_audit import read_document, write_document

ROOT = Path(__file__).resolve().parents[2]
STUDIO = Path(__file__).resolve().parent
PIPELINE_VERSION = ENGINE_VERSION
IGNORED = {'.yacreaderlibrary', '.nokturn-bubble-review', '.git', '.venv', '.runtime', 'praca', 'webtoon', 'webtoons', 'webtoony'}


def progress(**event):
    """Emit machine-readable events alongside human-readable logs."""
    print('@@' + json.dumps(event, ensure_ascii=False), flush=True)


def discover(root: Path):
    """Recognize volumes, skip caches and symlinks, and retain input-relative paths."""
    if any(part.casefold() in IGNORED for part in root.parts):
        return
    for directory, children, files in os.walk(root, followlinks=False):
        folder = Path(directory)
        children[:] = sorted(name for name in children if name.casefold() not in IGNORED and not (folder / name).is_symlink())
        if any(Path(name).suffix.casefold() in IMAGE_EXTENSIONS for name in files):
            yield folder
            children[:] = []
        for name in sorted(files):
            path = folder / name
            if path.suffix.casefold() in (ARCHIVE_EXTENSIONS | {'.pdf'}) and not is_bubble_package(path) and not path.is_symlink():
                yield path


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    os.replace(temporary, path)


def write_package(path: Path, manifest: dict, documents: list[dict]):
    """Publish one complete sidecar; a failed run cannot expose a partial package."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, allow_nan=False))
        for index, document in enumerate(documents):
            document['result'] = validate_result(document['result'])
            write_document(archive, f'pages/{index:05}.json', document)
    read_manifest(temporary)
    os.replace(temporary, path)


def copy_original(source: Path, destination: Path, checksum: str):
    """Never overwrite a different edition; preserve original archive bytes and metadata."""
    if source.resolve() == destination.resolve():
        raise ValueError('Folder GOTOWE nie może pokrywać się z WEJSCIE')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if source_sha256(destination) != checksum:
            raise ValueError(f'W GOTOWE istnieje inne wydanie: {destination}. Zachowano oba źródła bez nadpisania.')
        return
    if source.is_file():
        temporary = destination.with_name(destination.name + '.partial')
        shutil.copy2(source, temporary)
        if file_sha256(temporary) != checksum:
            raise ValueError('Kopia komiksu nie przeszła weryfikacji')
        os.replace(temporary, destination)
    else:
        temporary = destination.with_name(destination.name + '.partial')
        # Przerwana kopia pozostaje lokalnie; identyczne pliki nie są destrukcyjnie usuwane.
        def ignore(directory, names):
            return [name for name in names if name.casefold() in {'.nokturn-bubbles.zip', '.yacreaderlibrary'} or (Path(directory) / name).is_symlink()]
        shutil.copytree(source, temporary, dirs_exist_ok=True, ignore=ignore)
        if source_sha256(temporary) != checksum:
            raise ValueError('Kopia folderu komiksu nie przeszła weryfikacji')
        os.replace(temporary, destination)


def report_page(report: Path, index: int, image, document: dict):
    preview = image.copy()
    preview.thumbnail((1200, 6000))
    preview.save(report / f'{index:05}.jpg', quality=88)
    result = document['result']
    shapes = []
    suspects = {item['region_id'] for item in document.get('analysis', {}).get('text_check', {}).get('regions', [])
                if item.get('uncertain')}
    for bubble in result['bubbles']:
        x, y, w, h = (bubble[key] * 1000 for key in ('x', 'y', 'w', 'h'))
        polygons = bubble.get('polygons', [])
        if polygons:
            for polygon in polygons:
                points = ' '.join(f'{x + point["x"] * w:.2f},{y + point["y"] * h:.2f}' for point in polygon)
                css = ' class="suspect"' if bubble['id'] in suspects else ''
                shapes.append(f'<polygon{css} points="{points}"/>')
        else:
            css = 'fallback suspect' if bubble['id'] in suspects else 'fallback'
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{css}"/>')
        shapes.append(f'<text x="{x + 4}" y="{y + 12}">{bubble["order"]}</text>')
    flags = ''.join(f'<li>{html.escape(str(flag))}</li>' for flag in document['review']['flags'])
    return f'<section id="p{index}"><h2>Strona {index + 1} · {len(result["bubbles"])} dymków</h2><ul>{flags}</ul><div class="page"><img src="{index:05}.jpg"><svg viewBox="0 0 1000 1000" preserveAspectRatio="none">{"".join(shapes)}</svg></div></section>'


def write_report(report: Path, title: str, sections: list[str], flags: int):
    content = f'''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Bubble Studio — {html.escape(title)}</title><style>
body{{background:#14101c;color:#eee;font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 24px}}
h1,h2{{color:#ffc568}}a{{color:#ffc568}}section{{margin:40px 0}}li{{color:#ffc568}}
.page{{position:relative}}img{{width:100%;display:block}}svg{{position:absolute;inset:0;width:100%;height:100%}}
polygon,rect{{fill:#44dd9919;stroke:#10c677;stroke-width:2;vector-effect:non-scaling-stroke}}
.fallback{{stroke:#ff743c;stroke-dasharray:6 3}}text{{fill:#ff3b30;font-size:15px;font-weight:bold;paint-order:stroke;stroke:white;stroke-width:2px}}
.suspect{{stroke:#ffcf40;stroke-dasharray:4 4}}
</style><h1>{html.escape(title)}</h1><p>{len(sections)} stron; {flags} stron oznaczonych do kontroli.
Zielony: kontur. Pomarańczowy: prostokąt. Żółty przerywany: OCR nie potwierdził tekstu — sprawdź region. Numery: kolejność czytania.</p>
<p>Kontrola jakości: uruchom SPRAWDZ.bat i wybierz plik .nokturn-bubbles.zip.
Brak ostrzeżeń nie gwarantuje poprawnego rozpoznania. Sprawdź kolejność i kompletność tekstu także na tych stronach.</p>
{''.join(sections)}</html>'''
    (report / 'index.html').write_text(content, encoding='utf-8')


def process_comic(source: Path, relative: Path, output: Path, work: Path, analyzer, direction='ltr', layout='auto', webtoon=False,
                  include_free_text=False, quality='precise', force=False, discard_verified=False,
                  text_export='off', export_all_text=False, native_layers=None, reading_mode='auto'):
    """Checkpoint each native page, then verify and publish the exact source edition."""
    entries = list_image_entries(source)
    if not entries:
        raise ValueError('Brak stron w komiksie')
    initial_checksum = source_sha256(source)
    config = {'pipeline': PIPELINE_VERSION, 'direction': direction, 'layout': layout, 'webtoon': webtoon,
              'include_free_text': include_free_text, 'quality': quality,
              'models': getattr(analyzer, 'provenance', {}),
              'text_guard': getattr(analyzer, 'text_guard', 'off'),
              'recover_dialogue': getattr(analyzer, 'recover_dialogue', False)}
    if reading_mode != 'auto':
        config['reading_mode'] = reading_mode
    config = json.loads(json.dumps(config))
    destination = output / relative
    sidecar = package_path(destination)
    preserved = {}
    if destination.exists() and source_sha256(destination) != initial_checksum:
        raise ValueError(f'W GOTOWE istnieje inne wydanie: {destination}. Zachowano oba źródła bez nadpisania.')
    if sidecar.is_file() and destination.exists():
        try:
            existing = read_manifest(sidecar)
        except (BubblePackageError, zipfile.BadZipFile):
            logging.warning('Uszkodzony pakiet %s — odbudowuję; poprzedni zostanie zachowany w kopii', sidecar)
            existing = {'source': {'sha256': ''}}
        if existing['source']['sha256'] == initial_checksum and existing.get('config') == config and not force:
            print(f'  Gotowy pakiet: {relative} — pomijam, zachowuję korekty', flush=True)
            outcome={'comic': str(relative), 'status': 'skipped', 'pages': len(entries), 'sidecar': str(sidecar)}
            return optional_export(outcome,destination,text_export,export_all_text,native_layers)
        if existing['source']['sha256'] == initial_checksum and not discard_verified:
            with zipfile.ZipFile(sidecar) as archive:
                for page in existing['pages']:
                    document = read_document(archive, page['data'])
                    if document.get('review', {}).get('verified'):
                        validate_result(document['result'])
                        preserved[page['sha256']] = document
    key = hashlib.sha256((str(relative) + json.dumps(config, sort_keys=True) + initial_checksum).encode()).hexdigest()[:24]
    checkpoint = work / key
    report = output / '.nokturn-bubble-review' / key
    checkpoint.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    documents, pages, sections = [], [], []
    started = time.monotonic()
    for index, (name, size) in enumerate(entries):
        print(f'  {relative} · strona {index + 1}/{len(entries)}', flush=True)
        progress(kind='page', comic=str(relative), page=index+1, pages=len(entries))
        data = read_entry(source, name)
        page_hash = hashlib.sha256(data).hexdigest()
        stored = checkpoint / f'{index:05}.json'
        document = preserved.get(page_hash)
        if document is None and stored.is_file() and not force:
            try:
                cached = json.loads(stored.read_text(encoding='utf-8'))
                if cached['sha256'] == page_hash:
                    validate_result(cached['document']['result'])
                    document = cached['document']
            except (ValueError, KeyError, TypeError):
                pass
        with Image.open(io.BytesIO(data)) as raw:
            if raw.width * raw.height > 120_000_000:
                raise ValueError('Strona przekracza 120 megapikseli; podziel długi pasek')
            image = ImageOps.exif_transpose(raw).convert('RGB')
        if document is None:
            if hasattr(analyzer, 'quality'):
                analyzer.quality = quality
            document = analyzer.analyze(image, direction=direction, layout=layout, webtoon=webtoon,
                                        include_free_text=include_free_text,
                                        **({'reading_mode': reading_mode} if reading_mode != 'auto' else {}))
            document['result'] = validate_result(document['result'])
            atomic_json(stored, {'sha256': page_hash, 'document': document})
        pages.append({'index': index, 'name': name, 'size': size, 'sha256': page_hash, 'data': f'pages/{index:05}.json'})
        documents.append(document)
        sections.append(report_page(report, index, image, document))
        image.close()
    if source_sha256(source) != initial_checksum:
        raise ValueError('Komiks zmienił się podczas pracy. Uruchom ponownie po zakończeniu kopiowania.')
    manifest = {'format': 'nokturn-bubbles', 'version': 1, 'source': {'sha256': initial_checksum},
                'created_at': datetime.now(timezone.utc).isoformat(), 'config': config, 'pages': pages,
                'models': getattr(analyzer, 'provenance', {}), 'gpu': getattr(analyzer, 'device_info', {})}
    copy_original(source, destination, initial_checksum)
    if sidecar.exists():
        backup = sidecar.with_name(sidecar.name + '.before-upgrade-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        shutil.copy2(sidecar, backup)
    write_package(sidecar, manifest, documents)
    review_count = sum(bool(doc['review']['flags']) and not doc['review']['verified'] for doc in documents)
    write_report(report, source.name, sections, review_count)
    boxes = [box for document in documents for box in document['result']['bubbles']]
    outcome={'comic': str(relative), 'status': 'ready', 'pages': len(entries), 'review_pages': review_count,
            'contours': sum(bool(box.get('polygons')) for box in boxes), 'rectangles': sum(not box.get('polygons') for box in boxes),
            'verified_pages_preserved': len(preserved), 'sidecar': str(sidecar),
            'seconds': round(time.monotonic() - started, 1), 'report': str(report / 'index.html')}
    return optional_export(outcome,destination,text_export,export_all_text,native_layers)


def optional_export(outcome,source,format,all_text=False,native_layers=None):
    if format=='off':return outcome
    try:
        from .text_export import export_comic
        outcome['text_exports']=export_comic(source,format,all_text,native_layers=native_layers,
            progress=lambda page,pages:progress(kind='text-export',comic=source.name,page=page,pages=pages))
    except Exception as error:
        # A failure in this extra option must not mark a completed Nokturn
        # package as failed or discard the geometry that was just published.
        outcome['text_export_error']=str(error)
        logging.exception('Dymki gotowe; nie udał się dodatkowy eksport tekstu: %s',source)
    return outcome


def summary_report(output: Path, outcomes):
    """Publish a local library QA dashboard with escaped titles and safe file links."""
    from urllib.parse import quote
    directory = output / '.nokturn-bubble-review'
    rows = []
    for item in outcomes:
        link = ''
        if item.get('report'):
            target = Path(item['report']).relative_to(directory).as_posix()
            link = f'<a href="{quote(target)}">Otwórz strony</a>'
        for exported in item.get('text_exports', []):
            path=Path(exported)
            if path.suffix in {'.html','.txt','.md'}:
                target=os.path.relpath(path,directory).replace('\\','/')
                link+=f' · <a href="{quote(target)}">Tekst {html.escape(path.suffix[1:].upper())}</a>'
        if item.get('text_export_error'):
            link+=' · '+html.escape('Dymki gotowe; eksport tekstu nie powiódł się: '+item['text_export_error'])
        rows.append(f'<tr><td>{html.escape(item["comic"])}</td><td>{html.escape(item["status"])}</td>'
                    f'<td>{item.get("pages", "—")}</td><td>{item.get("contours", "—")} / {item.get("rectangles", "—")}</td>'
                    f'<td>{item.get("review_pages", "—")}</td><td>{link} {html.escape(item.get("error", ""))}</td></tr>')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'index.html').write_text('<!doctype html><html lang="pl"><meta charset="utf-8">'
        '<title>Bubble Studio — kolejka kontroli</title><style>body{background:#14101c;color:#eee;font:16px system-ui;padding:32px}'
        'td,th{padding:14px;text-align:left;border-bottom:1px solid #51435e}a{color:#ffc568}table{width:100%;border-collapse:collapse}</style>'
        '<h1>Kolejka kontroli Bubble Studio 2</h1><p>Kontur nie oznacza poprawnego konturu. Sprawdź też strony bez ostrzeżeń. '
        'Raport jest migawką automatu; korekty są w pakiecie/edytorze.</p><table><tr><th>Komiks</th><th>Stan</th>'
        '<th>Strony</th><th>Kontury / prostokąty</th><th>Strony z ostrzeżeniami</th><th>Podgląd</th></tr>' + ''.join(rows) + '</table></html>', encoding='utf-8')


def diagnostic():
    import torch
    print(f'Python {sys.version}; PyTorch {torch.__version__}; CUDA {torch.version.cuda}')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA niedostępne: sprawdź sterownik NVIDIA / instalację zależności')
    print(f'GPU: {torch.cuda.get_device_name(0)}; architektury: {torch.cuda.get_arch_list()}')
    with torch.inference_mode():
        matrix = torch.randn((512, 512), device='cuda')
        result = matrix @ matrix
        torch.cuda.synchronize()
        assert result.isfinite().all().item()
    print('Test rzeczywistego obliczenia na GPU: OK')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Nokturn Bubble Studio — przygotowanie lokalne na GPU')
    parser.add_argument('--input', type=Path, default=ROOT / 'WEJSCIE')
    parser.add_argument('--output', type=Path, default=ROOT / 'GOTOWE')
    parser.add_argument('--work', type=Path, default=ROOT / 'PRACA')
    parser.add_argument('--diagnostic', action='store_true')
    parser.add_argument('--offline', action='store_true', help='Bez pobierania modeli: wymagany istniejący cache')
    parser.add_argument('--reading-mode', choices=['auto', 'four_panel_strips'], default='auto', help='Układ historyjek: automatyczny albo pionowe 4koma')
    parser.add_argument('--quality', choices=['precise', 'fast'], default='precise')
    parser.add_argument('--extra-segmenter', dest='extra_segmenter', action='store_true', default=True,
                        help='Dodatkowy model masek (domyślnie włączony; GPL-3.0)')
    parser.add_argument('--no-extra-segmenter', dest='extra_segmenter', action='store_false')
    parser.add_argument('--include-free-text', action='store_true', help='Także tekst poza balonami, np. napisy okładek')
    parser.add_argument('--text-guard', choices=['off', 'review'], default='review',
                        help='Kontrola OCR: review wskazuje podejrzane regiony bez zmiany obrysów')
    parser.add_argument('--recover-dialogue', action='store_true',
                        help='Eksperymentalnie dodaj łacińskie wypowiedzi bez obramowania wewnątrz kadrów')
    parser.add_argument('--force', action='store_true', help='Przelicz niesprawdzone strony mimo checkpointów')
    parser.add_argument('--discard-verified', action='store_true', help='Także przelicz zatwierdzone ręczne korekty; wymaga --force')
    parser.add_argument('--text-export',choices=['off','html','txt','md'],default='off',help='Dodatkowy eksport tekstu, domyślnie wyłączony; HTML tworzy także TXT')
    parser.add_argument('--export-all-text',action='store_true',help='Tylko eksport: także pozostałe napisy poza listą dymków')
    parser.add_argument('--export-only',action='store_true',help='Eksportuj tekst gotowych pakietów bez uruchamiania modeli dymków')
    args = parser.parse_args(argv)
    if args.export_only:
        if args.text_export=='off':parser.error('--export-only wymaga --text-export')
        if not args.input.exists():raise ValueError('Nie istnieje wskazany komiks lub folder gotowych pakietów.')
        sources=[args.input] if args.input.is_file() or (args.input.is_dir() and package_path(args.input).is_file()) else list(discover(args.input))
        failures=0;completed=0
        for source in sources:
            if source.suffix.casefold()=='.pdf':continue
            outcome=optional_export(dict(comic=str(source),status='ready'),source,args.text_export,args.export_all_text)
            completed+=1
            failures+=bool(outcome.get('text_export_error'));print(json.dumps(outcome,ensure_ascii=False),flush=True)
        if not completed:raise ValueError('Nie znaleziono gotowych komiksów. Najpierw przygotuj dymki; sam PDF nie zawiera pakietu Nokturna.')
        return 1 if failures else 0
    if args.discard_verified and not args.force:
        parser.error('--discard-verified wymaga --force')
    os.environ.setdefault('HF_HOME', str(STUDIO / '.runtime' / 'models'))
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
    os.environ.setdefault('DO_NOT_TRACK', '1')
    os.environ.setdefault('YOLO_CONFIG_DIR', str(STUDIO / '.runtime' / 'yolo'))
    Path(os.environ['YOLO_CONFIG_DIR']).mkdir(parents=True, exist_ok=True)
    if args.offline:
        os.environ['HF_HUB_OFFLINE'] = '1'
    if args.diagnostic:
        diagnostic()
        return 0
    source_root, target_root = args.input.resolve(), args.output.resolve()
    if source_root == target_root or source_root in target_root.parents or target_root in source_root.parents:
        raise ValueError('WEJSCIE i GOTOWE muszą być oddzielnymi folderami')
    for category in ('Komiksy', 'Manga'):
        (source_root / category).mkdir(parents=True, exist_ok=True)
    sources = list(discover(source_root))
    if not sources:
        print(f'Brak komiksów. Dodaj CBZ/CBR, PDF lub foldery obrazów do: {source_root}')
        return 0
    target_root.mkdir(parents=True, exist_ok=True)
    lock = STUDIO / '.runtime' / 'processing.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    # Windows blokuje równoległy zapis do otwartego pliku; blokada znika także po awarii procesu.
    with lock.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0)
            stream.write(b'0')
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        from .models import GPUModels
        progress(kind='models', message='Pobieranie/wczytywanie lokalnych modeli')
        analyzer = GPUModels(quality=args.quality, extra_segmenter=args.extra_segmenter,
                             text_guard=args.text_guard, recover_dialogue=args.recover_dialogue)
        outcomes = []
        for source in sources:
            relative = source.relative_to(source_root)
            try:
                settings = series_settings(source, source_root, {'quality': args.quality, 'include_free_text': args.include_free_text, 'reading_mode': args.reading_mode})
                if settings.pop('skip'):
                    outcomes.append({'comic': str(relative), 'status': 'excluded'})
                else:
                    input_source=source;native_layers=None
                    if source.suffix.casefold()=='.pdf':
                        from .pdf_input import import_pdf
                        input_source,conversion,native_layers=import_pdf(source,args.work,include_text=args.text_export!='off',
                            notify=lambda page,pages:progress(kind='pdf-import',comic=str(relative),page=page,pages=pages))
                        relative=relative.with_name(source.stem+' (PDF).cbz')
                    outcome=process_comic(input_source, relative, target_root, args.work, analyzer,
                                          **settings, force=args.force, discard_verified=args.discard_verified,
                                          text_export=args.text_export,export_all_text=args.export_all_text,native_layers=native_layers)
                    if source.suffix.casefold()=='.pdf':outcome['pdf_source']=str(source)
                    outcomes.append(outcome)
            except Exception as exc:
                logging.exception('Nie udało się przygotować %s', relative)
                outcomes.append({'comic': str(relative), 'status': 'failed', 'error': str(exc)})
            atomic_json(target_root / '.nokturn-bubble-review' / 'summary.json', outcomes)
            summary_report(target_root, outcomes)
            progress(kind='comic', completed=len(outcomes), total=len(sources), **outcomes[-1])
        failed = sum(item['status'] == 'failed' for item in outcomes)
        print(f'Zakończono: {len(outcomes) - failed} gotowych / pominiętych, {failed} błędów. Wyniki: {target_root}', flush=True)
        return 1 if failed else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        logging.exception('Bubble Studio: %s', error)
        raise SystemExit(1)
