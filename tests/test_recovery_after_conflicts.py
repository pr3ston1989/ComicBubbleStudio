"""Exercise the complete analysis flow with controlled detector/segmenter outputs."""
import copy
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
import pytest

from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.models import GPUModels
from tools.bubble_studio.textcheck import TextCheck


class OCR:
    latin_dialogue = staticmethod(TextCheck.latin_dialogue)

    def locate(self, image):
        return [dict(box=[220, 150, 330, 190], text='I can hear you.',
                     score=.98, label=2, origin='ocr')]

    def read(self, image):
        return [dict(text='I can hear you.', score=.98)]


@pytest.mark.parametrize('direction', ['ltr', 'rtl'])
@pytest.mark.parametrize('recovery', [False, True])
def test_recovery_uses_surviving_geometry_and_keeps_existing_anchors(direction, recovery):
    image = Image.new('RGB', (400, 400), 'white')
    model = GPUModels.__new__(GPUModels)
    model.panels = SimpleNamespace(predict=lambda *a, **kw: [None])
    model.western = None
    model.text_checker = OCR()
    model.recover_dialogue = recovery
    model.text_guard = 'off'
    model.quality = 'precise'
    detections = [dict(label=0, score=.99, box=[20, 20, 100, 100]),
                  dict(label=0, score=.98, box=[140, 20, 210, 100]),
                  dict(label=1, score=.97, box=[40, 40, 70, 70]),
                  dict(label=1, score=.96, box=[160, 40, 190, 70]),
                  dict(label=2, score=.95, box=[220, 150, 330, 190])]
    model._detect = lambda *args: copy.deepcopy(detections)

    def segment(image, detection, *args):
        # The second mask has leaked out of its small detection into artwork,
        # covering both an existing balloon and a separate, genuine thought.
        bounds = [20, 20, 100, 100] if detection['score'] == .99 else [10, 10, 350, 220]
        region = rectangle(bounds, 400, 400, detection['score'], margin=0)
        region['polygons'] = [[dict(x=0, y=0), dict(x=1, y=0),
                               dict(x=1, y=1), dict(x=0, y=1)]]
        return region, None, {'method': 'controlled-test-mask'}

    model._segment = segment
    with patch('tools.bubble_studio.models.prediction_items', return_value=[]), \
         patch('tools.bubble_studio.quality_guard.region_guard', side_effect=lambda image, b, *a: (b, None)), \
         patch('tools.bubble_studio.tail_guard.screened_tail_guard', side_effect=lambda image, b, *a: (b, None)):
        document = model.analyze(image, direction=direction)
    result = document['result']
    assert document['analysis']['contour_conflicts']['pairs']
    assert len(result['bubbles']) == (3 if recovery else 2)
    assert all(not b.get('polygons') for b in result['bubbles'])
    anchors = list(document['analysis']['reading_anchors'].values())
    for expected_x in (.1, .4):
        assert any(a['x'] == expected_x and a['y'] == .1 and a['w'] == .075 for a in anchors)
    thoughts = document['analysis']['recovered_dialogue']
    assert len(thoughts) == (1 if recovery else 0)
    if recovery:
        assert thoughts[0]['box'] == [220, 150, 330, 190]
        assert thoughts[0]['requires_review']
    assert not document['review']['verified']
