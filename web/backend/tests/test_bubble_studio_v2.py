"""CPU-only regression tests for the portable Studio's quality and editing workflow."""

import copy
import json
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image
import pytest

from tools.bubble_studio.config import series_settings
from tools.bubble_studio.editing import polygon_box
from tools.bubble_studio.segmentation import ink_evidence, mask_in_region, prompt_points, validate_candidate, related_candidates, prediction_items
from tools.bubble_studio import runner
from web.backend.tests.test_comic_bubble_package import FakeAnalyzer, make_comic
from web.backend.comic_bubble_package import load_package, validate_result


def test_series_settings_inherit_and_allow_explicit_manhua_direction(tmp_path):
    parent = tmp_path / 'Manga' / 'Series'
    parent.mkdir(parents=True)
    source = parent / 'chapter.cbz'
    (tmp_path / 'bubble-studio.json').write_text('{"quality":"fast"}')
    (parent / 'bubble-studio.json').write_text('{"direction":"ltr", "layout":"columns"}')
    settings = series_settings(source, tmp_path)
    assert settings['direction'] == 'ltr' and settings['quality'] == 'fast' and settings['layout'] == 'columns'
    assert not settings['include_free_text']


@pytest.mark.parametrize('values', [{'typo': True}, {'skip': 'false'}, {'quality': 'magic'}, {'direction': 123}, []])
def test_bad_configuration_is_not_silently_ignored(tmp_path, values):
    (tmp_path / 'bubble-studio.json').write_text(json.dumps(values))
    with pytest.raises(ValueError):
        series_settings(tmp_path / 'comic.cbz', tmp_path)


def test_manga_defaults_rtl_and_other_categories_ltr(tmp_path):
    assert series_settings(tmp_path / 'Manga' / 'comic.cbz', tmp_path)['direction'] == 'rtl'
    assert series_settings(tmp_path / 'Manhua' / 'comic.cbz', tmp_path)['direction'] == 'ltr'


def test_mask_region_placement_clips_without_resize():
    candidate = {'origin': (50, 50), 'mask': np.ones((20, 30), np.uint8)}
    result = mask_in_region(candidate, (60, 40, 90, 80))
    assert result.shape == (40, 30)
    assert result.sum() == 400


def test_physical_page_edge_allowed_artificial_crop_edge_rejected():
    image = Image.new('RGB', (100, 100), 'white')
    mask = np.zeros((100, 100), np.uint8)
    mask[20:80, :60] = 1
    _, error, _ = validate_candidate(mask, [0, 20, 60, 80], [], (0, 0, 100, 100), (100, 100), image)
    assert error is None
    _, error, _ = validate_candidate(mask, [20, 20, 80, 80], [], (20, 0, 120, 100), (200, 100), image)
    assert 'sztucznej' in error


def lettering(dark=False):
    image = np.full((120, 160, 3), 0 if dark else 255, np.uint8)
    for offset in (40, 60, 80, 100):
        cv2.rectangle(image, (offset, 48), (offset+8, 66), (255, 255, 255) if dark else (0, 0, 0), -1)
    return Image.fromarray(image)


@pytest.mark.parametrize('dark', [False, True])
def test_pixel_evidence_supports_light_and_dark_balloons(dark):
    image = lettering(dark)
    texts = [{'box': [30, 30, 125, 85]}]
    evidence, reliable = ink_evidence(image, texts, (0, 0))
    assert reliable == 1 and np.count_nonzero(evidence) > 100
    mask = np.zeros((120, 160), np.uint8)
    cv2.ellipse(mask, (80, 60), (58, 34), 0, 0, 360, 255, -1)
    _, error, _ = validate_candidate(mask, [20, 25, 140, 95], texts, (0, 0, 160, 120), (160, 120), image)
    assert error is None
    mask[:, 100:] = 0
    _, error, _ = validate_candidate(mask, [20, 25, 140, 95], texts, (0, 0, 160, 120), (160, 120), image)
    assert 'piksele' in error


def test_sam_positive_points_and_negative_corners():
    points, labels = prompt_points([20, 20, 80, 80], [{'box': [30, 30, 60, 60]}], (0, 0, 100, 100), Image.new('RGB', (100, 100)))
    assert points[0] == [45, 45] and labels[0] == 1 and labels.count(0) == 4


def test_candidate_association_avoids_entire_page_mask():
    candidates = [{'box': [20, 20, 80, 80]}, {'box': [0, 0, 1000, 1000]}]
    assert related_candidates([20, 20, 80, 80], candidates) == candidates[:1]


def test_fast_pipeline_actually_uses_native_mask_instead_of_rectangle(monkeypatch):
    from tools.bubble_studio.models import GPUModels
    analyzer = GPUModels.__new__(GPUModels)
    analyzer.quality = 'fast'
    # Isolate the direct-mask branch from the independent colour generator.
    monkeypatch.setattr('tools.bubble_studio.models.enclosed_candidates', lambda *a, **kw: [])
    image = lettering()
    mask = np.zeros((120, 160), np.uint8)
    cv2.ellipse(mask, (80, 60), (58, 34), 0, 0, 360, 1, -1)
    # A validated contour now needs actual image edges. A blank white backdrop
    # cannot establish the outline of an arbitrary synthetic ellipse.
    rgb = np.array(image)
    cv2.ellipse(rgb, (80, 60), (58, 34), 0, 0, 360, (0, 0, 0), 2)
    image = Image.fromarray(rgb)
    candidate = {'mask': mask, 'origin': (0, 0), 'box': [20, 25, 140, 95], 'score': .9, 'method': 'native-test'}
    box, warning, diagnostics = analyzer._segment(image, candidate, [{'box': [30, 30, 125, 85]}], [candidate])
    assert box['polygons'] and warning is None and diagnostics['method'] == 'native-test'


def test_manual_polygon_retains_concavity_and_validates_for_nokturn():
    points = [(.1, .1), (.8, .1), (.8, .4), (.4, .4), (.4, .8), (.1, .8)]
    box = polygon_box(points, 'b1')
    assert len(box['polygon']) == 6
    result = {'width': 100, 'height': 100, 'direction': 'ltr', 'panels': [], 'bubbles': [box]}
    assert validate_result(result)['bubbles'][0]['polygons']


@pytest.mark.parametrize('points', [[(.1, .1), (.2, .2)], [(.1, .1), (.2, .2), (.3, .3)],
                                   [(float('nan'), .1), (.2, .2), (.3, .1)]])
def test_manual_contour_rejects_bad_vertices(points):
    with pytest.raises(ValueError):
        polygon_box(points, 'b1')


def test_manual_contour_rejects_crossing_edges():
    with pytest.raises(ValueError, match='przecinają'):
        polygon_box([(.1, .1), (.8, .8), (.1, .8), (.8, .2), (.9, .1)], 'b1')


def test_upgrading_pipeline_preserves_verified_edits_and_creates_backup(tmp_path, monkeypatch):
    source = make_comic(tmp_path / 'comic.cbz')
    analyzer = FakeAnalyzer()
    output, work = tmp_path / 'output', tmp_path / 'work'
    runner.process_comic(source, Path('comic.cbz'), output, work, analyzer)
    package = load_package(output / 'comic.cbz')
    with zipfile.ZipFile(package.sidecar) as archive:
        document = json.loads(archive.read('pages/00000.json'))
    document['review']['verified'] = True
    document['result']['bubbles'][0]['x'] = .25
    runner.write_package(package.sidecar, package.manifest, [document])
    monkeypatch.setattr(runner, 'PIPELINE_VERSION', 'test-next-version')
    outcome = runner.process_comic(source, Path('comic.cbz'), output, work, analyzer, force=True)
    assert analyzer.calls == 1
    assert outcome['verified_pages_preserved'] == 1
    assert load_package(output / 'comic.cbz').page(0)['result']['bubbles'][0]['x'] == .25
    assert list(output.glob('*.before-upgrade-*'))
    runner.process_comic(source, Path('comic.cbz'), output, work, analyzer, force=True, discard_verified=True)
    assert analyzer.calls == 2


def test_model_revision_tuples_round_trip_without_unnecessary_rebuild(tmp_path):
    source = make_comic(tmp_path / 'comic.cbz')
    analyzer = FakeAnalyzer()
    analyzer.provenance = {'model': ('repo', 'revision')}
    output, work = tmp_path / 'output', tmp_path / 'work'
    runner.process_comic(source, Path('comic.cbz'), output, work, analyzer)
    assert runner.process_comic(source, Path('comic.cbz'), output, work, analyzer)['status'] == 'skipped'
    assert analyzer.calls == 1


def test_every_edit_invalidates_verified_status_and_supports_undo_without_tk():
    from tools.bubble_studio.review import Reviewer
    reviewer = Reviewer.__new__(Reviewer)
    reviewer.index = 0
    reviewer.documents = [{'result': {'bubbles': []}, 'review': {'verified': True}}]
    reviewer.undo_stack, reviewer.redo_stack = [], []
    reviewer.load_page = lambda: None
    reviewer.edit()
    reviewer.documents[0]['result']['bubbles'].append({'id': 'b1'})
    assert not reviewer.documents[0]['review']['verified']
    reviewer.undo()
    assert reviewer.documents[0]['review']['verified'] and not reviewer.documents[0]['result']['bubbles']
    reviewer.redo()
    assert len(reviewer.documents[0]['result']['bubbles']) == 1


def test_gui_paths_are_literal_arguments_not_shell_commands():
    from tools.bubble_studio.gui import command
    argv = command('D:\\Comics & manga', 'D:\\output', 'D:\\work', 'precise', extra=True)
    assert 'D:\\Comics & manga' in argv and '--extra-segmenter' in argv


def test_gui_keeps_draining_progress_when_log_cannot_be_written(tmp_path, monkeypatch):
    import io
    import queue
    from types import SimpleNamespace
    from tools.bubble_studio import gui
    monkeypatch.setattr(gui, 'ROOT', tmp_path)
    def unavailable_log(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(Path, 'open', unavailable_log)
    studio = gui.Studio.__new__(gui.Studio)
    studio.events = queue.Queue()
    process = SimpleNamespace(stdout=io.StringIO('page progress\n'), wait=lambda: 0)
    studio.read_output(process)
    events = list(studio.events.queue)
    assert ('line', 'page progress') in events and events[-1] == ('done', 0)


def test_summary_escapes_untrusted_titles(tmp_path):
    runner.summary_report(tmp_path, [{'comic': '<script>alert(1)</script>', 'status': 'failed', 'error': '<bad>'}])
    text = (tmp_path / '.nokturn-bubble-review' / 'index.html').read_text(encoding='utf-8')
    assert '<script>' not in text and '&lt;script&gt;' in text


def test_corrupted_existing_sidecar_is_rebuilt_without_touching_comic(tmp_path):
    source = make_comic(tmp_path / 'comic.cbz')
    analyzer = FakeAnalyzer()
    output, work = tmp_path / 'output', tmp_path / 'work'
    runner.process_comic(source, Path('comic.cbz'), output, work, analyzer)
    package = load_package(output / 'comic.cbz')
    package.sidecar.write_bytes(b'broken')
    runner.process_comic(source, Path('comic.cbz'), output, work, analyzer)
    assert load_package(output / 'comic.cbz')
    assert (output / 'comic.cbz').read_bytes() == source.read_bytes()
    assert any(path.read_bytes() == b'broken' for path in output.glob('*.before-upgrade-*'))


def test_native_mask_extraction_rejects_tile_clipping_but_not_page_clipping():
    from types import SimpleNamespace
    torch = pytest.importorskip('torch')
    raw = np.zeros((100, 100), np.uint8)
    raw[20:80, 0:50] = 1
    prediction = SimpleNamespace(boxes=[SimpleNamespace(cls=torch.tensor([0]), conf=torch.tensor([.9]),
                                                       xyxy=torch.tensor([[0, 20, 50, 80]]))],
                                 masks=SimpleNamespace(data=torch.tensor(raw[None])), orig_shape=(100, 100))
    assert prediction_items(prediction, (20, 0), 'test', {0: 'bubble'}, (200, 100)) == []
    items = prediction_items(prediction, (0, 0), 'test', {0: 'bubble'}, (100, 100))
    assert items[0]['mask'].shape == (60, 50) and items[0]['origin'] == (0, 20)


def test_real_tk_editor_polygon_undo_and_save_roundtrip(tmp_path, monkeypatch):
    """Smoke real widgets while hidden; headless CI may skip the optional desktop check."""
    tk = pytest.importorskip('tkinter')
    from tools.bubble_studio.review import Reviewer, messagebox
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('Brak graficznego środowiska Tk')
    root.withdraw()
    source = make_comic(tmp_path / 'comic.cbz')
    runner.process_comic(source, Path('comic.cbz'), tmp_path / 'output', tmp_path / 'work', FakeAnalyzer())
    copied = tmp_path / 'output' / 'comic.cbz'
    try:
        editor = Reviewer(root, copied, load_package(copied))
        root.update_idletasks()
        editor.mode.set('Dodaj kontur')
        editor.vertices = [(.1, .1), (.8, .1), (.7, .6), (.2, .7)]
        editor.finish_polygon()
        assert len(editor.bubbles) == 2 and editor.bubbles[-1]['polygons']
        editor.verify()
        editor.reverse()
        assert not editor.documents[0]['review']['verified']
        editor.undo()
        assert editor.documents[0]['review']['verified']
        monkeypatch.setattr(messagebox, 'showinfo', lambda *args: None)
        monkeypatch.setattr(messagebox, 'showerror', lambda *args: pytest.fail(str(args)))
        editor.save()
        assert len(load_package(copied).page(0)['result']['bubbles']) == 2
    finally:
        root.destroy()


def test_real_tk_queue_widgets_update_without_starting_inference():
    tk = pytest.importorskip('tkinter')
    from tools.bubble_studio.gui import Studio
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip('Brak graficznego środowiska Tk')
    root.withdraw()
    try:
        studio = Studio(root)
        studio.events.put(('line', '@@{"kind":"page","comic":"test.cbz","page":2,"pages":10}'))
        studio.poll()
        root.update_idletasks()
        assert '2/10' in studio.state.get() and float(studio.bar['value']) == 20
        assert studio.extra.get() and studio.quality.get() == 'Dokładny'
    finally:
        root.destroy()
