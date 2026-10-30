"""Reproducible direct-mask smoke benchmark; counts are not an accuracy benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageOps, ImageDraw

from .geometry import contour_box, ordered_result
from .models import WESTERN, WESTERN_SHA256, PANELS, PANEL_SHA256, GPUModels, PIPELINE_VERSION
from .runner import ROOT, STUDIO, atomic_json, report_page, write_report
from .segmentation import prediction_items


def main(argv=None):
    parser = argparse.ArgumentParser(description='Test prawdziwych masek na obrazach — bez pomiaru accuracy')
    parser.add_argument('--images', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'PRACA' / 'benchmark')
    parser.add_argument('--model', choices=['western', 'manga', 'pipeline'], default='western')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cuda')
    parser.add_argument('--direction', choices=['ltr', 'rtl'], default='ltr')
    args = parser.parse_args(argv)
    os.environ.setdefault('HF_HOME', str(STUDIO / '.runtime' / 'models'))
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
    os.environ.setdefault('YOLO_CONFIG_DIR', str(STUDIO / '.runtime' / 'yolo'))
    Path(os.environ['YOLO_CONFIG_DIR']).mkdir(parents=True, exist_ok=True)
    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO, settings
    import torch
    torch.set_num_threads(4)
    settings.update({'sync': False})
    if args.model == 'pipeline':
        if args.device != 'cuda':
            parser.error('Pełny pipeline wymaga CUDA')
        model = GPUModels()
        repository = PIPELINE_VERSION
    else:
        repository, digest, filename = (WESTERN, WESTERN_SHA256, 'model.pt') if args.model == 'western' else (PANELS, PANEL_SHA256, 'best.pt')
        weights = hf_hub_download(repository[0], filename, revision=repository[1])
        if hashlib.sha256(Path(weights).read_bytes()).hexdigest() != digest:
            raise ValueError('Nieprawidłowa suma kontrolna wag benchmarku')
        model = YOLO(weights)
    args.output.mkdir(parents=True, exist_ok=True)
    sections, results = [], []
    for index, path in enumerate(sorted(args.images.iterdir())):
        if path.suffix.casefold() not in {'.png', '.jpg', '.jpeg', '.webp'}:
            continue
        print(f'Test {path.name}', flush=True)
        started = time.monotonic()
        with Image.open(path) as raw:
            image = ImageOps.exif_transpose(raw).convert('RGB')
        if args.model == 'pipeline':
            document = model.analyze(image, direction=args.direction)
            bubbles = document['result']['bubbles']
            regions = len(bubbles)
        else:
            prediction = model.predict(image, imgsz=1280, conf=.35, retina_masks=True, device=args.device, verbose=False)[0]
            items = prediction_items(prediction, (0, 0), args.model, {0 if args.model == 'western' else 2: 'bubble'})
            bubbles = [contour_box(item['mask'] * 255, item['origin'], *image.size, item['score']) for item in items if 'mask' in item]
            regions = len(items)
            document = {'result': ordered_result([], bubbles, *image.size, args.direction, 'auto'),
                        'review': {'verified': False, 'flags': ['Surowe maski modelu — bez SAM i walidacji, wymagają oceny wzrokowej']}}
        atomic_json(args.output / f'{index:05}.json', document)
        sections.append(report_page(args.output, index, image, document))
        preview = image.copy()
        preview.thumbnail((1200, 4000))
        drawing = ImageDraw.Draw(preview)
        for box in document['result']['bubbles']:
            if not box.get('polygons'):
                drawing.rectangle((box['x']*preview.width,box['y']*preview.height,
                                   (box['x']+box['w'])*preview.width,(box['y']+box['h'])*preview.height),
                                  outline='#ff8800',width=3)
            for polygon in box.get('polygons', []):
                points = [((box['x']+point['x']*box['w'])*preview.width,
                           (box['y']+point['y']*box['h'])*preview.height) for point in polygon]
                drawing.line(points + points[:1], fill='#00ff88', width=3)
        preview.save(args.output / f'{index:05}-overlay.png')
        preview.close()
        image.close()
        results.append({'image': path.name, 'regions': regions, 'contours': sum(bool(b.get('polygons')) for b in bubbles),
                        'rectangles':sum(not b.get('polygons') for b in bubbles), 'seconds': round(time.monotonic()-started, 2),
                        'result': document['result']})
    atomic_json(args.output / 'benchmark.json', {'model': repository, 'device': args.device, 'results': results,
                                               'note': 'Smoke test; no ground-truth accuracy measurement'})
    title = 'Pełny pipeline ' + PIPELINE_VERSION if args.model == 'pipeline' else 'Porównanie surowych masek ' + args.model
    write_report(args.output, title, sections, len(sections))
    print(json.dumps([{k: v for k, v in item.items() if k != 'result'} for item in results], ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
