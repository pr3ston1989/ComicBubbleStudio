"""Local OCR review isolated from contour generation; never deletes existing regions."""
from __future__ import annotations

import hashlib
import math
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from threading import Lock, local
import numpy as np
from .geometry import rectangle, intersection, area, deduplicate

OCR_SHA256 = {
    'ch_PP-OCRv4_det_infer.onnx': 'd2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9',
    'ch_PP-OCRv4_rec_infer.onnx': '48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b',
    'ch_ppocr_mobile_v2.0_cls_infer.onnx': 'e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c',
}
EFFECT_WORDS={'slam','clench','pose','splash','bang','boom','chop','snort','thud','click','tap','whoosh','creak',
              'chrp','skraw','rub','szur','stuk','bum','trzask'}


def catalog_page(rows):
    """Conservative blocker for extra recovery, never deletion of detected speech."""
    compact=re.sub(r'[^a-z0-9]','',' '.join(r['text'] for r in rows).casefold())
    markers=('learnmoreonline','highlightedtitles','deluxeedition','allrightsreserved',
             'ratedteen','firstissue','oneshot','dispatch')
    return sum(marker in compact for marker in markers)>=2 or compact.count('deluxeedition')>=2


class TextCheck:
    """Use bundled, pinned OCR weights; never interpret OCR failure as proof of no text."""
    def __init__(self):
        import rapidocr_onnxruntime
        from rapidocr_onnxruntime import RapidOCR
        folder = Path(rapidocr_onnxruntime.__file__).parent / 'models'
        hashes = {name: hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in OCR_SHA256}
        if hashes != OCR_SHA256:
            raise RuntimeError('Nieprawidłowa suma kontrolna lokalnego modelu OCR')
        self.engine = RapidOCR(intra_op_num_threads=4, inter_op_num_threads=1)
        self.provenance = {'package': 'rapidocr-onnxruntime==1.4.4',
                           'weights': hashes}
        self._cache = {}
        self._cache_lock = Lock()
        self._engine_lock = Lock()
        self._workers = local()
        # Each RapidOCR instance has mutable preprocessing state. Share only
        # the immutable weights on disk, never an inference instance.
        self._executor = (
            ThreadPoolExecutor(max_workers=2, thread_name_prefix='studio-ocr')
            if (os.cpu_count() or 1) >= 8 else None
        )

    def read(self, image):
        with self._engine_lock:
            return self._read(image, self.engine)

    def _read(self, image, engine):
        crop = image.copy()
        crop.thumbnail((900, 900))
        if min(crop.size) < 40:
            scale = 40 / max(1, min(crop.size))
            crop = crop.resize((round(crop.width*scale), round(crop.height*scale)))
        rgb = np.asarray(crop)
        key = hashlib.sha256(rgb.tobytes() + str(rgb.shape).encode()).digest()
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
        result, _ = engine(rgb[..., ::-1].copy(), use_cls=False)
        rows = [{'text': str(r[1]), 'score': float(r[2]),
                 'box': [float(min(p[0] for p in r[0]))/crop.width,
                         float(min(p[1] for p in r[0]))/crop.height,
                         float(max(p[0] for p in r[0]))/crop.width,
                         float(max(p[1] for p in r[0]))/crop.height]}
                for r in result or []]
        with self._cache_lock:
            if len(self._cache) >= 1024:
                self._cache.clear()
            return self._cache.setdefault(key, rows)

    def _read_regions(self, image, regions):
        if self._executor is None or len(regions) < 2:
            return [self.read(image.crop(box)) for box in regions]

        image.load()

        def read_region(box):
            if not hasattr(self._workers, 'engine'):
                from rapidocr_onnxruntime import RapidOCR
                self._workers.engine = RapidOCR(intra_op_num_threads=4, inter_op_num_threads=1)
            return self._read(image.crop(box), self._workers.engine)

        # Keep page and region order deterministic even when workers finish
        # out of order. Drain the batch before returning or propagating errors.
        jobs = [self._executor.submit(read_region, box) for box in regions]
        try:
            return [job.result() for job in jobs]
        finally:
            wait(jobs)

    def locate(self, image):
        """Independent OCR sweep: RT-DETR misses must not be invisible to recovery.

        Overlapping native tiles retain small dialogue. Ignore lines clipped at
        artificial tile edges; the neighbouring tile sees the complete line.
        """
        output = []
        edge, stride = 1200, 960
        xs = sorted({0, max(0,image.width-edge), *range(0,max(1,image.width-edge),stride)})
        ys = sorted({0, max(0,image.height-edge), *range(0,max(1,image.height-edge),stride)})
        regions = [(x, y, min(image.width, x+edge), min(image.height, y+edge))
                   for y in ys for x in xs]
        for region, rows in zip(regions, self._read_regions(image, regions)):
            x, y, right, bottom = region
            width, height = right-x, bottom-y
            for row in rows:
                if row['score'] < .85:
                    continue
                a, b, c, d = row['box']
                if ((x and a < .005) or (y and b < .005)
                        or (right < image.width and c > .995) or (bottom < image.height and d > .995)):
                    continue
                output.append({'box':[x+a*width,y+b*height,x+c*width,y+d*height],
                               'score':row['score'], 'text':row['text'], 'label':2, 'origin':'ocr'})
        return deduplicate(output, .7)

    def locate_context(self, image):
        """Retain full prose lines on large scans as well as native detail.

        This separate pass is used only by the semantic page reader. It cannot
        change coverage, masks or recovery decisions in the primary detector.
        """
        scaled=image.copy();scaled.thumbnail((2200,2200))
        sx,sy=image.width/scaled.width,image.height/scaled.height
        return [dict(row,box=[v*factor for v,factor in zip(row['box'],(sx,sy,sx,sy))])
                for row in self.locate(scaled)]

    @staticmethod
    def readable(rows):
        return any(r['score'] >= .75 and any(c.isalpha() for c in r['text'])
                   or r['score'] >= .85 and any(c in '!?…' for c in r['text']) for r in rows)

    @staticmethod
    def latin_dialogue(rows):
        text = ' '.join(r['text'] for r in rows if r['score'] >= .85)
        letters = sum(c.isalpha() and 'LATIN' in unicodedata.name(c,'') for c in text)
        words = re.findall(r'[^\W\d_]{2,}', text, re.UNICODE)
        if words and all(word.casefold() in EFFECT_WORDS for word in words):
            return False
        # A lone CLENCH/SLAM is usually an effect, not a recovered utterance.
        return letters >= 3 and (len(words) >= 2 or any(c in '.!?…' for c in text))

    def review(self, image, document, mode='review'):
        """Preserve every existing region: OCR failure is only a review signal."""
        if mode != 'review':
            raise ValueError('Nieznany tryb kontroli tekstu')
        result = document['result']
        checks = []
        bubbles = result['bubbles']
        boxes = [pixel_box(bubble, image.size) for bubble in bubbles]
        for bubble, box, rows in zip(bubbles, boxes, self._read_regions(image, boxes)):
            readable = self.readable(rows)
            uncertain = not readable
            if uncertain:
                flag = (f'OCR nie potwierdził tekstu w regionie {bubble["id"]}; '
                        'sprawdź rysunek, małe litery lub sam znak interpunkcyjny')
                document['review']['flags'].append(flag)
            checks.append({'region_id': bubble['id'], 'box': box, 'ocr': rows,
                           'uncertain': uncertain})
        document.setdefault('analysis', {})['text_check'] = {'mode': mode, 'regions': checks}
        document['review']['flags'] = list(dict.fromkeys(document['review']['flags']))
        return document


def pixel_box(bubble, size):
    w, h = size
    return (max(0, math.floor(bubble['x']*w)), max(0, math.floor(bubble['y']*h)),
            min(w, math.ceil((bubble['x']+bubble['w'])*w)),
            min(h, math.ceil((bubble['y']+bubble['h'])*h)))


def split_text_columns(checker, image, bubbles):
    """Separate text-only rectangles spanning clearly independent columns.

    Never split a balloon contour. Every OCR row must be confident and retained;
    each side needs multiple lines, dialogue evidence and a wide empty gutter.
    Whitespace inside a single line or between stacked paragraphs is insufficient.
    """
    output, audit = [], []
    for bubble in bubbles:
        output.append(bubble)
        if bubble.get('type') != 'text' or bubble.get('polygons') or bubble.get('polygon'):
            continue
        bounds = pixel_box(bubble, image.size)
        width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
        if min(width,height) < 40 or width < 1.8*height:
            continue
        rows = checker.read(image.crop(bounds))
        if len(rows)<4 or any(r.get('score',0)<.85 or not r.get('box') for r in rows):
            continue
        if any(not all(math.isfinite(v) for v in r['box'])
               or not (0<=r['box'][0]<r['box'][2]<=1 and 0<=r['box'][1]<r['box'][3]<=1)
               for r in rows):
            continue
        line_height=float(np.median([(r['box'][3]-r['box'][1])*height for r in rows]))
        gap=max(2*line_height,.1*width)
        columns=[]
        for row in sorted(rows,key=lambda r:r['box'][0]):
            a,b,c,d=row['box']
            if not columns or (a-columns[-1]['box'][2])*width>=gap:
                columns.append({'box':[a,b,c,d],'rows':[row]})
            else:
                col=columns[-1];x,y,z,w=col['box']
                col['box']=[min(a,x),min(b,y),max(c,z),max(d,w)]
                col['rows'].append(row)
        if not 2<=len(columns)<=4:
            continue
        if any(len(c['rows'])<2 or not checker.latin_dialogue(c['rows'])
               or sum(ch.isalpha() for r in c['rows'] for ch in r['text'])<12 for c in columns):
            continue
        # Side-by-side multi-line blocks must share a meaningful vertical span.
        if any(min(a['box'][3],b['box'][3])-max(a['box'][1],b['box'][1])
               < .35*min(a['box'][3]-a['box'][1],b['box'][3]-b['box'][1])
               for a,b in zip(columns,columns[1:])):
            continue
        replacements=[]
        for col in columns:
            a,b,c,d=col['box']
            target=[bounds[0]+a*width,bounds[1]+b*height,bounds[0]+c*width,bounds[1]+d*height]
            replacements.append(rectangle(target,*image.size,bubble['confidence'],'text',margin=6))
        output[-1:]=replacements
        audit.append({'reason':'separate-text-columns','original':bubble.copy(),
                      'columns':columns,'replacements':replacements,
                      'gutter_min_pixels':gap,'requires_review':True})
    return output, audit


def recover_panel_dialogue(checker, image, texts, bubbles, panels):
    """Recover narration/thoughts with OCR, including frameless manga panels.

    Existing geometry is immutable. Free text stays a text region and never
    becomes a made-up balloon. Ambiguous scene labels still require review.
    """
    from .refinement import contour_covers_text
    added, audit, candidates = [], [], []
    def covered(box):
        text = {'box':box}
        return any(contour_covers_text(b,text,image.size) if b.get('polygons')
                   else intersection(box,pixel_box(b,image.size))/max(1,area(box))>.60
                   for b in [*bubbles,*added])
    for text in texts:
        if text['label'] != 2 or text['score'] < .55:
            continue
        if not covered(text['box']):
            candidates.append({**text,'origin':'detector'})
    # Recover blocks that the specialised detector never proposed. Group only
    # adjacent, similarly sized OCR lines; never bridge a column/panel boundary.
    all_lines=checker.locate(image)
    if catalog_page(all_lines):
        return [], [{'reason':'catalog-page','status':'recovery-skipped',
                     'note':'Wiele oznak katalogu/reklamy. Zachowano dotychczasowe dymki; nie dodano OCR.'}]
    lines = [row for row in all_lines if not covered(row['box'])]
    blocks = []
    for row in sorted(lines,key=lambda r:(r['box'][1],r['box'][0])):
        a,b,c,d = row['box']; height=max(1,d-b)
        panel = max(panels,key=lambda p:intersection(row['box'],pixel_box(p,image.size)),default=None)
        panel_id = id(panel) if panel and intersection(row['box'],pixel_box(panel,image.size))/max(1,area(row['box']))>.5 else None
        target = None
        for block in reversed(blocks):
            u,v,w,z = block['box']
            overlap = max(0,min(c,w)-max(a,u))/max(1,min(c-a,w-u))
            previous_height = block['last_height']
            if (block['panel']==panel_id and -.15*height <= b-z <= .8*max(height,previous_height)
                    and overlap >= .5 and .55 <= height/previous_height <= 1.8):
                target = block
                break
        if target is None:
            blocks.append({'box':list(row['box']),'rows':[row], 'panel':panel_id,'last_height':height})
        else:
            target['box']=[min(a,target['box'][0]),target['box'][1],max(c,target['box'][2]),max(d,target['box'][3])]
            target['rows'].append(row)
            target['last_height']=height
    for block in blocks:
        # Detector blocks have better semantic grouping; prefer them where they
        # already cover an OCR line. Uncovered lines remain independent evidence.
        if any(intersection(block['box'],t['box'])/max(1,area(block['box']))>.6 for t in candidates):
            continue
        candidates.append({'box':block['box'],'label':2,'score':min(r['score'] for r in block['rows']),
                           'origin':'ocr', 'rows':block['rows']})
    for text in sorted(candidates,key=lambda t:(t['origin']=='ocr',-t['score'])):
        if len(bubbles)+len(added)>=128:
            break
        box=text['box']
        if covered(box):
            continue
        panel_overlap = max((intersection(box, pixel_box(p, image.size))/max(1, area(box))
                             for p in panels), default=0)
        rows = text.get('rows') or checker.read(image.crop(tuple(map(int, box))))
        if not checker.latin_dialogue(rows):
            continue
        words=re.findall(r'[^\W\d_]{2,}', ' '.join(r['text'] for r in rows), re.UNICODE)
        # Isolated OCR words without a detector are frequently labels/effects.
        # Frameless narration needs stronger evidence and story context.
        if (text['origin']=='ocr' and len(words)<3) or (panel_overlap<.8 and (not bubbles or len(words)<3)):
            continue
        added.append(rectangle(box, *image.size, text['score'], 'text', margin=6))
        audit.append({'box': box, 'ocr': rows, 'origin':text['origin'],
                      'reason':'free-text-inside-panel' if panel_overlap>=.8 else 'frameless-dialogue',
                      'requires_review':True})
    return added, audit
