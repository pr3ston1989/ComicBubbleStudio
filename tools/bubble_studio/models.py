"""Pinned specialist detectors and SAM 2.1, running exclusively on the local GPU."""

from __future__ import annotations

import hashlib
import contextlib
import numpy as np

from .geometry import deduplicate, intersection, area, padded_box, rectangle, contour_box, ordered_result
from .segmentation import mask_in_region, validate_candidate, prompt_points, related_candidates, prediction_items
from .refinement import enclosed_candidates, candidate_rank, contour_covers_text

DETECTOR = ('ogkalu/comic-text-and-bubble-detector', '16e8a622f91fabc6b5b65c96d32d1183f8843546')
SEGMENTER = ('facebook/sam2.1-hiera-large', '665f8e2ad61cf5f53d65644ff27c8ee525124610')
PANELS = ('ShadowB/Manga109-panel-balloon-text-yolov26-segmentation', '3a860269ee0beb43ce9f31d82c7851441eb178ae')
PANEL_SHA256 = '0b4376e426fa96af3976afa6a2602421dacf2dec96ef87b4a44f5e8d4971cb6f'
WESTERN = ('Jzahrani/yolov8m_seg-speech-bubble', '3d6da7def774c927d56b03cfc37f982204c138db')
WESTERN_SHA256 = '200141c44d4153662050531905ec3354d1d6302c28939dbbb019c037250ed610'
PIPELINE_VERSION = 'bubble-studio-2.8.0'


def _load_detector(device='cuda'):
    """Load RT-DETR v2 with arguments supported by the pinned Transformers version."""
    from transformers import AutoModelForObjectDetection
    # RT-DETR v2 nie obsługuje disable_custom_kernels (parametr wersji v1).
    return AutoModelForObjectDetection.from_pretrained(
        DETECTOR[0], revision=DETECTOR[1], use_safetensors=True,
        trust_remote_code=False).to(device).eval()


class GPUModels:
    """Load fixed, verified weights once; no cloud inference or remote Python code."""

    def __init__(self, quality='precise', extra_segmenter=True, text_guard='review', recover_dialogue=False):
        import torch
        from huggingface_hub import hf_hub_download
        from transformers import AutoImageProcessor, Sam2Model, Sam2Processor
        from ultralytics import YOLO, settings
        settings.update({'sync': False})
        self.torch = torch
        self.quality = quality
        if text_guard not in {'off', 'review'}:
            raise ValueError('Nieznany tryb kontroli tekstu')
        self.text_guard, self.recover_dialogue = text_guard, recover_dialogue
        self.text_checker = None
        self.western = None
        self.crop_segmenter = None
        self.page_context = None
        self.scene_context = None
        if not torch.cuda.is_available():
            raise RuntimeError('Brak działającego CUDA. Zaktualizuj sterownik NVIDIA i uruchom DIAGNOSTYKA.bat.')
        props = torch.cuda.get_device_properties(0)
        print(f'GPU: {props.name}; VRAM: {props.total_memory / 1024 ** 3:.1f} GB', flush=True)
        if props.total_memory < 10 * 1024 ** 3:
            raise RuntimeError('Ten profil jakości wymaga co najmniej 10 GB VRAM. Zalecane 16 GB.')
        torch.set_num_threads(6)
        torch.backends.cuda.matmul.allow_tf32 = True
        print('Wczytywanie RT-DETR, SAM 2.1 large i detektora kadrów…', flush=True)
        self.processor = AutoImageProcessor.from_pretrained(
            DETECTOR[0], revision=DETECTOR[1], trust_remote_code=False, use_fast=False)
        self.detector = _load_detector()
        self.sam_processor = Sam2Processor.from_pretrained(SEGMENTER[0], revision=SEGMENTER[1])
        self.sam = Sam2Model.from_pretrained(SEGMENTER[0], revision=SEGMENTER[1], use_safetensors=True).to('cuda').eval()
        weights = hf_hub_download(PANELS[0], 'best.pt', revision=PANELS[1])
        with open(weights, 'rb') as stream:
            if hashlib.sha256(stream.read()).hexdigest() != PANEL_SHA256:
                raise RuntimeError('Nieprawidłowa suma kontrolna modelu kadrów. Odmowa wczytania.')
        self.panels = YOLO(weights)
        if extra_segmenter:
            weights = hf_hub_download(WESTERN[0], 'model.pt', revision=WESTERN[1])
            with open(weights, 'rb') as stream:
                if hashlib.sha256(stream.read()).hexdigest() != WESTERN_SHA256:
                    raise RuntimeError('Nieprawidłowa suma kontrolna dodatkowego segmentera')
            self.western = YOLO(weights)
            from .crop_segmenter import CropSegmenter
            self.crop_segmenter = CropSegmenter()
        self.provenance = {'detector': DETECTOR, 'segmenter': SEGMENTER, 'panels': PANELS}
        if self.western:
            self.provenance['extra_segmenter'] = WESTERN
            from .crop_segmenter import MODEL
            self.provenance['crop_segmenter'] = MODEL
        self.device_info = {'name': props.name, 'vram_bytes': props.total_memory, 'torch': torch.__version__, 'cuda': torch.version.cuda}
        if text_guard != 'off' or recover_dialogue:
            from .textcheck import TextCheck
            self.text_checker = TextCheck()
            self.provenance['text_check'] = self.text_checker.provenance
        if quality=='precise' and recover_dialogue and text_guard=='review':
            from .page_context import SemanticPage
            self.page_context=SemanticPage()
            self.provenance['page_context']=self.page_context.provenance
            from .scene_model import ScenePage
            self.scene_context=ScenePage()
            self.provenance['scene_context']=self.scene_context.provenance

    def _autocast(self):
        if self.torch.cuda.is_bf16_supported():
            return self.torch.autocast('cuda', dtype=self.torch.bfloat16)
        return contextlib.nullcontext()

    def _detect(self, image, region):
        x1, y1, x2, y2 = region
        crop = image.crop(region)
        inputs = self.processor(images=crop, return_tensors='pt').to('cuda')
        with self.torch.inference_mode(), self._autocast():
            outputs = self.detector(**inputs)
        detected = self.processor.post_process_object_detection(outputs, threshold=0.35, target_sizes=[(crop.height, crop.width)])[0]
        result = []
        for label, score, box in zip(detected['labels'].cpu().tolist(), detected['scores'].float().cpu().tolist(), detected['boxes'].float().cpu().tolist()):
            bx1, by1, bx2, by2 = box
            # Nie wnosimy uciętych dymków z granicy kafla; pełny wycinek lub drugi kafel mają pierwszeństwo.
            if (x1 > 0 and bx1 < 3) or (y1 > 0 and by1 < 3) or (x2 < image.width and bx2 > crop.width - 3) or (y2 < image.height and by2 > crop.height - 3):
                continue
            mapped = [max(x1, bx1 + x1), max(y1, by1 + y1), min(x2, bx2 + x1), min(y2, by2 + y1)]
            if area(mapped) >= 16:
                result.append({'label': label, 'score': float(score), 'box': mapped})
        return result

    def _segment(self, image, detection, texts, candidates):
        """Compare direct masks with prompted SAM; retry larger crops instead of inventing an outline."""
        box = detection['box']
        failures, accepted = [], []
        region = padded_box(box, image.width, image.height, .45)
        crop = image.crop(region)
        for padding in (.45, 1.2, 2.2, 4.0):
            color_region = padded_box(box, image.width, image.height, padding)
            color_crop = image.crop(color_region)
            for candidate in enclosed_candidates(color_crop, box, texts, color_region, image.size):
                # A detector can return each lobe of a physically joined balloon.
                # Its true connected interior can exceed one detection box.
                validation_box = candidate['box'] if candidate['area_ratio'] > 1.65 else box
                mask, error, metrics = validate_candidate(candidate['mask'], validation_box, texts, color_region, image.size, color_crop)
                if error:
                    failures.append('enclosed-color: ' + error)
                else:
                    metrics['color_stability'] = candidate['stability']
                    metrics['detection_area_ratio'] = candidate['area_ratio']
                    accepted.append((candidate['score'], mask, color_region, candidate['method'], metrics))
            if any(item[3] == 'enclosed-color' for item in accepted):
                break
        for candidate in related_candidates(box, candidates):
            if 'mask' not in candidate:
                continue
            mask, error, metrics = validate_candidate(mask_in_region(candidate, region), box, texts, region, image.size, crop)
            if error:
                failures.append(candidate['method'] + ': ' + error)
            else:
                accepted.append((candidate['score'], mask, region, candidate['method'], metrics))
        if getattr(self, 'crop_segmenter', None) is not None:
            for padding in (.15, .45, 1.2):
                crop_region = padded_box(box, *image.size, padding)
                model_crop = image.crop(crop_region)
                mask, error, metrics = validate_candidate(self.crop_segmenter.predict(model_crop), box, texts,
                                                         crop_region, image.size, model_crop)
                if error:
                    failures.append('manet: ' + error)
                else:
                    accepted.append((.85, mask, crop_region, 'manet-crop', metrics))
                    break
        if self.quality == 'fast' and accepted:
            best = self._best_candidate(accepted, image)
            if best[4]['boundary_support'] >= .65:
                return contour_box(best[1], best[2], *image.size, detection['score']), None, {'method': best[3], **best[4]}
        # A narrow crop can produce an apparently confident body while omitting
        # a long tail entirely. Give SAM room to see the complete balloon.
        for attempt, padding in enumerate((.75, 1.5) if self.quality == 'precise' else (.45,)):
            region = padded_box(box, image.width, image.height, padding)
            crop = image.crop(region)
            local_box = [box[0]-region[0], box[1]-region[1], box[2]-region[0], box[3]-region[1]]
            points, labels = prompt_points(box, texts, region, crop)
            kwargs = {'input_boxes': [[local_box]]}
            if attempt:
                kwargs.update(input_points=[[points]], input_labels=[[labels]])
            inputs = self.sam_processor(images=crop, return_tensors='pt', **kwargs).to('cuda')
            with self.torch.inference_mode(), self._autocast():
                outputs = self.sam(**inputs, multimask_output=True)
            masks = self.sam_processor.post_process_masks(outputs.pred_masks.float().cpu(), inputs['original_sizes'].cpu())[0]
            masks = masks.reshape(-1, crop.height, crop.width).numpy()
            scores = outputs.iou_scores.float().cpu().reshape(-1).tolist()
            for index in sorted(range(len(scores)), key=lambda index: scores[index], reverse=True):
                if scores[index] < .60:
                    failures.append('Niska pewność SAM')
                    continue
                mask, error, metrics = validate_candidate(masks[index], box, texts, region, image.size, crop)
                if error:
                    failures.append(error)
                    continue
                accepted.append((scores[index], mask, region, f'sam2-attempt-{attempt+1}', metrics))
            if accepted and self._best_candidate(accepted, image)[4]['boundary_support'] >= .65:
                break
        if accepted:
            # Pewność nie jest pomiarem prawidłowości. Rozbieżność modeli zawsze trafia do kontroli.
            best = self._best_candidate(accepted, image)
            if best[4]['boundary_support'] < .65:
                # Do not trace a guessed shape over faces/art when no candidate
                # follows image edges. Keep the actual text visible for review.
                text_box = [min(t['box'][0] for t in texts), min(t['box'][1] for t in texts),
                            max(t['box'][2] for t in texts), max(t['box'][3] for t in texts)]
                return rectangle(text_box, *image.size, detection['score'], 'text', margin=6), 'Słabe oparcie konturu w obrazie; zachowano obszar tekstu do kontroli', {
                    'method': 'text-fallback', 'boundary_support': best[4]['boundary_support'],
                    'rejections': list(dict.fromkeys(failures))}
            warning = None
            for other in accepted:
                aligned = mask_in_region({'mask': other[1], 'origin': other[2]}, best[2]) > 0
                selected = best[1] > 0
                overlap = np.count_nonzero(aligned & selected) / max(1, np.count_nonzero(aligned | selected))
                if overlap < .65:
                    warning = 'Segmentery nie zgadzają się co do obrysu; sprawdź kontur i ogonek'
            return contour_box(best[1], best[2], *image.size, detection['score']), warning, {
                'method': best[3], 'candidates': len(accepted), 'rejections': list(dict.fromkeys(failures)), **best[4]}
        return rectangle(box, *image.size, detection['score']), 'Brak bezpiecznej maski; zachowano prostokąt', {
            'method': 'rectangle', 'rejections': list(dict.fromkeys(failures))}

    @staticmethod
    def _best_candidate(accepted, image):
        ranked = []
        for candidate in accepted:
            confidence, mask, region, method, metrics = candidate
            rank, support = candidate_rank(mask, image.crop(region), confidence, metrics)
            metrics['boundary_support'] = round(support, 4)
            metrics['selection_score'] = round(rank, 4)
            ranked.append((rank, candidate))
        return max(ranked, key=lambda item: item[0])[1]

    def _recover_text(self, image, text):
        """Recover only bounded image interiors, not arbitrary artwork around text."""
        detection = padded_box(text['box'], *image.size, .35)
        for padding in (.6, 1.5, 2.5):
            region = padded_box(detection, *image.size, padding)
            crop = image.crop(region)
            for candidate in enclosed_candidates(crop, detection, [text], region, image.size):
                mask, error, metrics = validate_candidate(candidate['mask'], candidate['box'], [text], region, image.size, crop)
                if not error:
                    result = contour_box(mask, region, *image.size, text['score'])
                    return result, {'method':'enclosed-text-recovery', 'detection_box':text['box'],
                                    'color_stability':candidate['stability'], **metrics}
        return None, None

    def analyze(self, image, direction='ltr', layout='auto', webtoon=False, include_free_text=False):
        """Use page, overlapping strip tiles, and panel crops before local contour refinement."""
        context=getattr(self,'page_context',None)
        if context is not None:
            context.park()
            self.detector.to('cuda');self.sam.to('cuda')
        width, height = image.size
        panel_items, secondary, mask_candidates = [], [], []
        panel_regions = [(0, 0, width, height)]
        if width * height > 12_000_000:
            # Maska każdego obiektu w rozdzielczości ogromnego skanu mogłaby wyczerpać VRAM.
            overview = self.panels.predict(image, imgsz=1280, conf=.35, device=0, retina_masks=False,
                                           max_det=128, verbose=False, half=False)[0]
            panel_items.extend(prediction_items(overview, (0, 0), 'manga-yolo26', {0: 'panel'}))
            edge, stride = 1536, 1152
            xs = sorted(set([max(0, width-edge), *range(0, max(1, width-edge), stride)]))
            ys = sorted(set([max(0, height-edge), *range(0, max(1, height-edge), stride)]))
            panel_regions = [(x, y, min(width, x+edge), min(height, y+edge)) for y in ys for x in xs]
        elif height > width * 2:
            step, tile = max(1, int(width * 1.05)), int(width * 1.5)
            panel_regions = [(0, top, width, min(height, top + tile)) for top in range(0, height, step)]
        for region in panel_regions:
            prediction = self.panels.predict(image.crop(region), imgsz=1280, conf=0.35, device=0,
                                             retina_masks=True, max_det=128, verbose=False, half=False)[0]
            items = prediction_items(prediction, region, 'manga-yolo26', {0: 'panel', 2: 'bubble'}, image.size)
            if len(panel_regions) == 1:
                panel_items.extend(item for item in items if item['label'] == 'panel' and area(item['box']) >= 36)
            secondary.extend(item for item in items if item['label'] == 'bubble' and area(item['box']) >= 36)
            mask_candidates.extend(item for item in items if item['label'] == 'bubble')
            if self.western:
                prediction = self.western.predict(image.crop(region), imgsz=1280, conf=.35, device=0,
                                                  retina_masks=True, max_det=128, verbose=False, half=False)[0]
                extras = prediction_items(prediction, region, 'western-yolov8', {0: 'bubble'}, image.size)
                secondary.extend(extras)
                mask_candidates.extend(extras)
        panel_items = deduplicate(panel_items)[:64]
        regions = [(0, 0, width, height)] + [padded_box(item['box'], width, height, 0.03) for item in panel_items]
        # Drugi przebieg w stałej skali znajduje małe dymki także bez wykrytych ramek.
        if width > 1200 or height > 1600:
            edge, stride = 1024, 704
            x_starts = sorted(set([0, max(0, width - edge), *range(0, max(1, width - edge), stride)]))
            y_starts = sorted(set([0, max(0, height - edge), *range(0, max(1, height - edge), stride)]))
            regions.extend((left, top, min(width, left + edge), min(height, top + edge)) for top in y_starts for left in x_starts)
        # Długie obrazy wymagają kafli; pojedyncze zmniejszenie do 640 px gubi drobny tekst.
        if height > width * 1.8:
            tile = int(width * 1.3)
            regions.extend((0, top, width, min(height, top + tile)) for top in range(0, height, max(1, int(tile * 0.7))))
        detections = []
        for region in dict.fromkeys(regions):
            detections.extend(self._detect(image, region))
        balloons = deduplicate([item for item in detections if item['label'] == 0] + secondary)[:128]
        texts = deduplicate([item for item in detections if item['label'] in {1, 2}])
        bubbles, flags, used_text, diagnostics, unconfirmed = [], [], set(), [], []
        geometry_checks=[]
        for number, balloon in enumerate(balloons, 1):
            inside = [item for item in texts if intersection(item['box'], balloon['box']) / max(1, area(item['box'])) > 0.7]
            if inside and any(all(contour_covers_text(existing, text, image.size) for text in inside) for existing in bubbles):
                used_text.update(id(item) for item in inside)
                continue
            used_text.update(id(item) for item in inside)
            if not inside:
                # Circular artwork is frequently classified as a balloon. Do
                # not make it a reading stop without any supporting text box.
                unconfirmed.append({'box':balloon['box'], 'score':balloon['score']})
                flags.append(f'Pominięto obiekt przy ({round(balloon["box"][0])}, {round(balloon["box"][1])}) bez potwierdzonego tekstu; sprawdź możliwe przeoczenie dymka')
                continue
            box, error, detail = self._segment(image, balloon, inside, mask_candidates)
            from .quality_guard import region_guard
            box,check=region_guard(image,box,inside,panel_items,getattr(self,'text_checker',None),detail['method'])
            if check:
                geometry_checks.append(check)
                flags.append('Sprawdź klasyfikację tekstu i obrysu: '+check['reason'])
            if box is None:
                continue
            from .tail_guard import screened_tail_guard
            box,tail_check=screened_tail_guard(image,box,inside)
            if tail_check:
                geometry_checks.append(tail_check)
                flags.append('Odtworzono ogonek na podstawie obrazu; sprawdź jego zakończenie')
            box['_reading_box'] = rectangle([min(t['box'][0] for t in inside), min(t['box'][1] for t in inside),
                                             max(t['box'][2] for t in inside), max(t['box'][3] for t in inside)],
                                            width, height, balloon['score'], margin=0)
            detail['detection_box'] = balloon['box']
            detail['supporting_texts'] = [{k:t[k] for k in ('box','label','score')} for t in inside]
            diagnostics.append(detail)
            bubbles.append(box)
            if box.get('polygons'):
                used_text.update(id(text) for text in texts if contour_covers_text(box, text, image.size))
            if error:
                flags.append(f'Dymek przy ({round(balloon["box"][0])}, {round(balloon["box"][1])}): {error}')
        for text in texts:
            if id(text) not in used_text and len(bubbles) < 128 and (text['label'] == 1 or include_free_text):
                if text['label'] == 1:
                    recovered, detail = self._recover_text(image, text)
                    if recovered:
                        bubbles.append(recovered)
                        diagnostics.append(detail)
                        used_text.update(id(other) for other in texts if contour_covers_text(recovered, other, image.size))
                        flags.append('Odzyskano kontur z tekstu bez wykrytego balonu; sprawdź kompletność')
                        continue
                bubbles.append(rectangle(text['box'], width, height, text['score'], 'text', margin=6))
                if text['label'] == 1:
                    flags.append('Tekst dymka bez wykrytego balonu; sprawdź brakujący kontur')
        if not bubbles:
            flags.append('Nie wykryto dymków: możliwa okładka, ilustracja lub przeoczenie modelu')
        if len(balloons) == 128:
            flags.append('Osiągnięto limit dymków na stronie; podziel zbyt długi pasek webtoon')
        panels = [rectangle(item['box'], width, height, item['score'], margin=0) for item in panel_items]
        recovered_dialogue = []
        checker = getattr(self, 'text_checker', None)
        text_splits=[]
        if checker and getattr(self, 'recover_dialogue', False) and not include_free_text:
            from .textcheck import split_text_columns
            bubbles,text_splits=split_text_columns(checker,image,bubbles)
            if text_splits:
                flags.append('Rozdzielono kolumny tekstu bez dymków; sprawdź podział i kolejność myśli')
        # Recovery must see the geometry that will actually be published.
        # A rejected, overlapping mask can cover unrelated thoughts; checking
        # coverage before this guard silently loses those words afterwards.
        # Recovered regions are rectangles, so they cannot introduce a new
        # polygon conflict and do not need a second conflict pass.
        from .quality_guard import guard_conflicts
        conflicts=guard_conflicts(bubbles,width,height)
        if conflicts['pairs']:
            flags.append('Kontury nachodziły na siebie; zachowano obszary tekstu do ręcznej kontroli')
        if checker and getattr(self, 'recover_dialogue', False) and not include_free_text:
            from .textcheck import recover_panel_dialogue
            added, recovered_dialogue = recover_panel_dialogue(checker, image, texts, bubbles, panels)
            bubbles.extend(added)
            if added:
                flags.append('Dodano tekst bez obramowania; sprawdź myśli, narrację, SFX i napisy scenografii')
            if any(a.get('reason')=='catalog-page' for a in recovered_dialogue):
                flags.append('Prawdopodobny katalog lub reklama: pominięto dodawanie tekstu OCR; sprawdź istniejące regiony')
        reading_anchors={id(b):{k:b.get('_reading_box',b)[k] for k in ('x','y','w','h')} for b in bubbles}
        result = ordered_result(panels, bubbles, width, height, direction, 'rows' if webtoon else layout)
        if len(panel_items) > 1 and any(box.get('panel_id') is None for box in result['bubbles']):
            flags.append('Sprawdź kolejność dymków poza kadrami')
        document = {'result': result, 'review': {'flags': list(dict.fromkeys(flags)), 'verified': False},
                'analysis': {'pipeline': PIPELINE_VERSION, 'quality': self.quality, 'balloons': diagnostics,
                             'unconfirmed_detections': unconfirmed,
                             'ignored_free_text': sum(item['label'] == 2 and id(item) not in used_text for item in texts)
                             if not include_free_text else 0,
                             'recovered_dialogue': recovered_dialogue}}
        document['analysis']['geometry_checks']=geometry_checks
        document['analysis']['text_splits']=text_splits
        document['analysis']['reading_anchors']={b['id']:reading_anchors[id(b)] for b in result['bubbles']}
        document['analysis']['contour_conflicts']=conflicts
        if checker and getattr(self, 'text_guard', 'off') != 'off':
            checker.review(image, document, self.text_guard)
        if checker and getattr(self, 'recover_dialogue', False) and not include_free_text:
            from .content_filter import apply_content_filter
            apply_content_filter(document,checker.locate(image))
        from .stroke_guard import recover_page_outlines
        refined = False
        if context is not None and checker and not include_free_text:
            # Never keep the language model's large weights and segmentation
            # workspaces competing for VRAM. Only one stage is active at once.
            self.detector.to('cpu');self.sam.to('cpu');self.torch.cuda.empty_cache()
            try:
                document=context.review(image,document,checker)
                document=recover_page_outlines(image,document)
                refined = True
                from .page_finish import refine_semantic_page
                document=refine_semantic_page(image,document,checker,context)
            finally:context.park()
        if not refined:
            document=recover_page_outlines(image,document)
        if self.quality=='precise' and checker and getattr(self,'recover_dialogue',False) and not include_free_text:
            from .page_finish import refine_native_page
            document=refine_native_page(image,document,checker)
            from .finish243 import refine_additional_page
            document=refine_additional_page(image,document,checker)
            from .finish251 import refine_page
            document=refine_page(image,document,checker,context)
            from .finish252 import refine_page as refine_final_page
            document=refine_final_page(image,document,context)
            from .finish253 import refine_page as refine_readable_text
            document=refine_readable_text(image,document,checker,context)
            scene=getattr(self,'scene_context',None)
            if scene is not None:
                from .finish260 import refine_page as refine_scene_page
                document=refine_scene_page(image,document,checker,context,scene)
            from .closed_body import refine as refine_closed_body
            document=refine_closed_body(image,document,checker)
            from .native_ink import refine as refine_native_ink
            document=refine_native_ink(image,document)
            from .native_panel_order import refine as refine_native_panel_order
            document=refine_native_panel_order(image,document)
            from .tail_tip import annotate_tail_tips
            document=annotate_tail_tips(image,document)
        return document
