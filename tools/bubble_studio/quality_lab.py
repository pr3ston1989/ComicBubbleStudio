"""Seeded archive sampling and resumable, local visual regression laboratory."""
from __future__ import annotations
import argparse
import hashlib
import html
import io
import json
import random
import time
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from web.backend.comic_archive import list_image_entries, read_entry
from .runner import atomic_json, discover


def sample(source, output, seed=20261027, books=12, pages=2, exclude=()):
    """Stratify books by folder convention; reserve whole books for holdout."""
    rng = random.Random(seed)
    excluded={str(Path(p).resolve()).casefold() for p in exclude}
    excluded_series={str(Path(p).resolve().parent).casefold() for p in exclude if Path(p).resolve().parent!=source.resolve()}
    candidates = sorted((p for p in discover(source) if str(p.resolve()).casefold() not in excluded
                         and str(p.resolve().parent).casefold() not in excluded_series), key=lambda p: str(p).casefold())
    groups = {'ltr': [], 'rtl': []}
    for path in candidates:
        # The supplied library has chapter updates in a separate manga tree.
        manga = any('manga' in p.casefold() or 'shonen' in p.casefold() for p in path.parts)
        groups['rtl' if manga else 'ltr'].append(path)
    samples, errors = [], []
    for direction, pool in groups.items():
        rng.shuffle(pool)
        chosen = 0
        seen_series = set()
        for path in pool:
            if chosen >= books // 2:
                break
            book_start=len(samples)
            try:
                family=str(path.parent.relative_to(source)) if path.parent!=source else path.stem
                if family in seen_series:
                    continue
                entries = list_image_entries(path)
                # Include interior pages; covers/ads are sampled separately by --seed.
                indexes = list(range(1, max(1, len(entries)-1)))
                if not indexes:
                    continue
                split = 'holdout' if chosen % 3 == 2 else 'development'
                for page in sorted(rng.sample(indexes, min(pages, len(indexes)))):
                    name = entries[page][0]
                    data = read_entry(path, name)
                    key = hashlib.sha256(data).hexdigest()
                    filename = f'{len(samples):03}-{key[:12]}.png'
                    output.mkdir(parents=True, exist_ok=True)
                    with Image.open(io.BytesIO(data)) as raw:
                        image = ImageOps.exif_transpose(raw).convert('RGB')
                        image.save(output / filename)
                    samples.append({'image': filename, 'archive': str(path), 'entry': name,
                                    'page': page+1, 'direction': direction, 'split': split,
                                    'sha256': key, 'image_sha256': hashlib.sha256((output/filename).read_bytes()).hexdigest()})
                chosen += 1
                seen_series.add(family)
            except Exception as exc:
                # Do not let a partly unreadable book skew the book/page quota.
                # Unreferenced preview files are harmless and retained for diagnosis.
                samples=samples[:book_start]
                errors.append({'archive': str(path), 'error': str(exc)})
    manifest = {'seed': seed, 'samples': samples, 'errors': errors,
                'note': 'Whole books held out. Inspect before claiming accuracy; no automatic ground truth.'}
    atomic_json(output / 'sample.json', manifest)
    return manifest


def overlay(image, document, path):
    preview = image.copy()
    preview.thumbnail((1500, 2500))
    draw = ImageDraw.Draw(preview)
    bubbles = document['result']['bubbles']
    centers = []
    for b in bubbles:
        x,y,w,h = [b[k]*size for k,size in zip(('x','y','w','h'), (preview.width,preview.height,preview.width,preview.height))]
        color = '#1ddba1' if b.get('polygons') else '#ffad42'
        for polygon in b.get('polygons', []):
            points = [(x+p['x']*w, y+p['y']*h) for p in polygon]
            draw.line(points+points[:1], fill=color, width=2)
        if not b.get('polygons'):
            draw.rectangle((x,y,x+w,y+h), outline=color, width=2)
        draw.rectangle((x,y,x+29,y+23), fill='#211832')
        draw.text((x+4,y+3), str(b['order']), fill='white')
        centers.append((x+w/2,y+h/2))
    preview.save(path)


def run(images, output, split='all', recovery=False):
    from .models import GPUModels, PIPELINE_VERSION
    manifest = json.loads((images/'sample.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    model = GPUModels(recover_dialogue=recovery)
    if getattr(model,'page_context',None) is not None:model.page_context.strict=True
    sources=[Path(__file__).with_name(name+'.py') for name in
             ('models','geometry','segmentation','crop_segmenter','refinement','textcheck','quality_guard','tail_guard','config','content_filter',
              'page_context','context_layout','context_prompts','stroke_guard',
              'page_finish','strip_reader','publishing_filter','body_order','compound_guard',
              'native_enclosures','thin_bridges','color_stroke_guard','tail_continuation',
                'finish243','enclosure_repair','lobe_order','thought_dots',
                'finish251','native_body','exact_duplicates','editorial_audit','promotion_audit','panel_gutters',
                'finish252','nonstory_mask','finish253','short_text','panel_background','finish260','scene_objects','scene_model','scene_gutters','retail_promotion','native_margin','closed_body','native_ink','native_ink_graph','native_ink_evidence','native_panel_order','tail_tip','control_buttons','native_framed_order','strip_heading_order','framed_strip_order','native_wide_frame_order','vertical_body_order')]
    sources+=[Path(__file__).resolve().parents[2]/'assets/context-model.json',Path(__file__).resolve().parents[2]/'assets/scene-model.json']
    sources+=[Path(__file__).resolve().parents[2]/'web'/'backend'/'comic_smartview_layout.py']
    signature=hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sources)).hexdigest()
    records = []
    for item in manifest['samples']:
        if split != 'all' and item['split'] != split:
            continue
        key = Path(item['image']).stem
        if hashlib.sha256((images/item['image']).read_bytes()).hexdigest()!=item['image_sha256']:
            raise ValueError('Zmieniono stronę próbki; ponowne porównanie nie byłoby wiarygodne')
        result_file = output / (key+'.json')
        expected = {'pipeline': PIPELINE_VERSION, 'recovery': recovery, 'sha256': item['image_sha256'], 'code_sha256':signature}
        if result_file.exists():
            document = json.loads(result_file.read_text(encoding='utf-8'))
            if document.get('lab') != expected:
                raise ValueError('Nie mieszaj konfiguracji w raporcie: wybierz nowy folder wynikowy')
        else:
            print(f'{key} {item["direction"]} {item["split"]}', flush=True)
            started = time.monotonic()
            with Image.open(images/item['image']) as image:
                document = model.analyze(image.convert('RGB'), direction=item['direction'])
            document['lab'] = expected
            document['seconds'] = round(time.monotonic()-started, 3)
            atomic_json(result_file, document)
        with Image.open(images/item['image']) as image:
            overlay(image, document, output/(key+'-overlay.png'))
        records.append({**item, 'data': key+'.json', 'overlay': key+'-overlay.png',
                        'regions': len(document['result']['bubbles']),
                        'text_regions': sum(b['type']=='text' for b in document['result']['bubbles']),
                        'rectangles': sum(not b.get('polygons') for b in document['result']['bubbles']),
                        'seconds': document['seconds'], 'flags': document['review']['flags']})
        atomic_json(output/'results.json', {'pipeline': PIPELINE_VERSION, 'recovery': recovery, 'pages': records})
    report(images, output, records)
    print(json.dumps({'pages':len(records), 'regions':sum(r['regions'] for r in records),
                      'text':sum(r['text_regions'] for r in records), 'seconds':sum(r['seconds'] for r in records)}), flush=True)


def report(images, output, records=None):
    if records is None:
        records = json.loads((output/'results.json').read_text(encoding='utf-8'))['pages']
    import os
    for record in records:
        record['original'] = Path(os.path.relpath(images/record['image'], output)).as_posix()
    payload = json.dumps(records, ensure_ascii=False).replace('<', '\\u003c')
    template = Path(__file__).with_name('quality_lab.html').read_text(encoding='utf-8')
    (output/'index.html').write_text(template.replace('/*RECORDS*/[]', payload), encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Losowanie stron i lokalne laboratorium jakości')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('sample')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=20261027)
    p.add_argument('--books', type=int, default=12)
    p.add_argument('--pages', type=int, default=2)
    p.add_argument('--exclude-manifest',type=Path)
    p = sub.add_parser('run')
    p.add_argument('--images', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--split', choices=['all','development','holdout'], default='all')
    p.add_argument('--recover-dialogue', action='store_true')
    p = sub.add_parser('cycle')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--books', type=int, default=12)
    p.add_argument('--pages', type=int, default=2)
    p.add_argument('--exclude-manifest',type=Path)
    p.add_argument('--recover-dialogue', action='store_true')
    args = parser.parse_args(argv)
    if args.command in {'sample','cycle'}:
        if args.books < 2 or args.pages < 1:
            parser.error('Wymagane co najmniej dwie książki i jedna strona')
        sample_output=args.output/'sample' if args.command=='cycle' else args.output
        if (sample_output/'sample.json').exists():
            parser.error('Próbka już istnieje. Wznów poleceniem run albo wybierz nowy folder.')
        seed=args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
        excluded=[]
        if args.exclude_manifest:
            excluded=[item['archive'] for item in json.loads(args.exclude_manifest.read_text(encoding='utf-8'))['samples']]
        result = sample(args.source, sample_output, seed, args.books, args.pages, excluded)
        print(json.dumps({'pages':len(result['samples']), 'errors':result['errors']}, ensure_ascii=False))
        if not result['samples']:
            parser.error('Nie znaleziono stron do testowania; sprawdź folder i błędy archiwów')
        if args.command=='cycle':
            run(sample_output,args.output/'results',recovery=args.recover_dialogue)
    else:
        run(args.images, args.output, args.split, args.recover_dialogue)


if __name__ == '__main__':
    main()
