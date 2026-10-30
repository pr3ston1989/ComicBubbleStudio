"""Portable-package security, scanner exclusions, and inference-free API integration."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from web.backend.comic_bubble_package import BubblePackageError, load_package, package_path, read_manifest, validate_result
from web.backend.comic_scanner import _issue_candidates, _series_folders
from tools.bubble_studio.geometry import contour_box, ordered_result, validated_mask
from tools.bubble_studio.runner import discover, process_comic, write_package


def simple_result():
    return ordered_result([], [{'x': .2, 'y': .2, 'w': .4, 'h': .3, 'confidence': .9}], 200, 300, 'ltr', 'auto')


def make_comic(path):
    stream = io.BytesIO()
    Image.new('RGB', (200, 300), 'white').save(stream, 'PNG')
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('001.png', stream.getvalue())
    return path


class FakeAnalyzer:
    calls = 0

    def analyze(self, image, **kwargs):
        self.calls += 1
        return {'result': simple_result(), 'review': {'flags': ['Sprawdź kontur'], 'verified': False}}


@pytest.fixture
def prepared(tmp_path):
    source = make_comic(tmp_path / 'comic.cbz')
    analyzer = FakeAnalyzer()
    result = process_comic(source, Path('comic.cbz'), tmp_path / 'output', tmp_path / 'work', analyzer)
    return source, tmp_path / 'output' / 'comic.cbz', analyzer, result


def test_round_trip_original_unchanged_review_flag_and_complete_result(prepared):
    source, copied, analyzer, report = prepared
    assert copied.read_bytes() == source.read_bytes()
    package = load_package(copied)
    assert package is not None
    payload = package.page(0)
    assert payload['source'] == 'external'
    assert payload['status'] == 'ready'
    assert payload['review_required'] is True
    assert len(payload['result']['bubbles']) == 1
    assert Path(report['report']).is_file()
    assert analyzer.calls == 1


def test_studio_22_round_trip_preserves_rtl_multiple_contours_and_recovered_text(tmp_path):
    """New diagnostics are optional metadata; rendering still uses v1 geometry."""
    from tools.bubble_studio.config import ENGINE_VERSION
    from copy import deepcopy
    source = make_comic(tmp_path / 'manga.cbz')
    outline = [{'x': 0, 'y': 0}, {'x': 1, 'y': 0}, {'x': 1, 'y': 1}, {'x': 0, 'y': 1}]
    result = ordered_result([], [
        {'x': .1, 'y': .1, 'w': .4, 'h': .2, 'confidence': .9,
         'polygons': [outline, [{**point, 'x': point['x'] * .3} for point in outline]]},
        {'x': .6, 'y': .6, 'w': .2, 'h': .2, 'confidence': .9, 'type': 'text'},
    ], 200, 300, 'rtl', 'columns')
    result = validate_result(result)
    document = {'result': result, 'review': {'flags': ['OCR: sprawdź region b1'], 'verified': False},
                'analysis': {'text_check': {'mode': 'review', 'regions': [{'region_id': 'b1', 'uncertain': True}]},
                             'recovered_dialogue': [{'text': 'Hello there!'}]}}

    class Analyzer:
        text_guard = 'review'
        recover_dialogue = True

        def analyze(self, image, **kwargs):
            return deepcopy(document)

    output = tmp_path / 'output'
    process_comic(source, Path('manga.cbz'), output, tmp_path / 'work', Analyzer(), direction='rtl', layout='columns')
    package = load_package(output / 'manga.cbz')
    assert package.manifest['config']['pipeline'] == ENGINE_VERSION
    payload = package.page(0)
    assert payload['result'] == result
    assert payload['review_required']
    assert payload['review_flags'] == document['review']['flags']
    assert payload['source'] == 'external'
    assert len(next(box for box in result['bubbles'] if box['type'] == 'bubble')['polygons']) == 2
    assert 'polygons' not in next(box for box in result['bubbles'] if box['type'] == 'text')


def test_second_run_skips_and_preserves_review(prepared, tmp_path):
    source, copied, analyzer, _ = prepared
    package = load_package(copied)
    with zipfile.ZipFile(package.sidecar) as archive:
        document = json.loads(archive.read('pages/00000.json'))
    document['review']['verified'] = True
    write_package(package.sidecar, package.manifest, [document])
    outcome = process_comic(source, Path('comic.cbz'), copied.parent, tmp_path / 'work', analyzer)
    assert outcome['status'] == 'skipped'
    assert analyzer.calls == 1
    assert load_package(copied).page(0)['review_required'] is False


def test_checkpoint_survives_missing_output_package(prepared, tmp_path):
    source, copied, analyzer, _ = prepared
    package_path(copied).unlink()
    process_comic(source, Path('comic.cbz'), copied.parent, tmp_path / 'work', analyzer)
    assert analyzer.calls == 1
    assert load_package(copied)


def test_modified_source_rejects_sidecar_and_never_overwrites_output(prepared, tmp_path):
    source, copied, analyzer, _ = prepared
    with zipfile.ZipFile(source, 'a') as archive:
        archive.writestr('metadata.txt', 'different edition')
    previous = copied.read_bytes()
    with pytest.raises(ValueError, match='inne wydanie'):
        process_comic(source, Path('comic.cbz'), copied.parent, tmp_path / 'work', analyzer)
    assert copied.read_bytes() == previous
    with zipfile.ZipFile(copied, 'a') as archive:
        archive.writestr('metadata.txt', 'modified')
    assert load_package(copied) is None


def test_bad_page_hash_disables_package_instead_of_permanently_claiming_ready(prepared):
    _, copied, _, _ = prepared
    package = load_package(copied)
    with zipfile.ZipFile(package.sidecar) as archive:
        document = json.loads(archive.read('pages/00000.json'))
    package.manifest['pages'][0]['sha256'] = '0' * 64
    write_package(package.sidecar, package.manifest, [document])
    package = load_package(copied)
    with pytest.raises(BubblePackageError):
        package.page(0)
    assert load_package(copied) is None


@pytest.mark.parametrize('mutation', [
    lambda result: result.update(width=-1),
    lambda result: result['bubbles'][0].update(x=float('nan')),
    lambda result: result['bubbles'][0].update(w=2),
    lambda result: result['bubbles'][0].update(polygons=[[{}, {}, {}]]),
    lambda result: result['bubbles'][0].update(polygons=[[None, None, None]]),
    lambda result: result['bubbles'][0].update(id='javascript:alert(1)'),
])
def test_rejects_unsafe_geometry(mutation):
    result = simple_result()
    mutation(result)
    with pytest.raises(BubblePackageError):
        validate_result(result)


def test_zip_traversal_and_duplicate_members_rejected(prepared):
    _, copied, _, _ = prepared
    sidecar = package_path(copied)
    with zipfile.ZipFile(sidecar, 'a') as archive:
        archive.writestr('../outside.txt', 'no extraction permitted')
    with pytest.raises(BubblePackageError):
        read_manifest(sidecar)


def test_scanner_never_indexes_sidecars_or_review_images(prepared):
    _, copied, _, _ = prepared
    assert _issue_candidates(copied.parent) == [copied]
    assert _series_folders(copied.parent) == [copied.parent]


def test_webtoon_and_yacreader_are_not_external_processing_inputs(tmp_path):
    for category in ('Manga', 'Webtoon', '.yacreaderlibrary'):
        (tmp_path / category).mkdir()
        make_comic(tmp_path / category / 'sample.cbz')
    assert list(discover(tmp_path)) == [tmp_path / 'Manga' / 'sample.cbz']


def test_mask_rejects_cut_text_and_truncated_edges():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 1
    detection = [20, 20, 80, 80]
    valid, error = validated_mask(mask, detection, [{'box': [30, 30, 70, 70]}], (0, 0))
    assert error is None and valid is not None
    _, error = validated_mask(mask, detection, [{'box': [10, 10, 90, 90]}], (0, 0))
    assert 'tekst' in error
    mask[0, 50] = 1
    _, error = validated_mask(mask, detection, [], (0, 0))
    assert error


def test_preserves_separate_native_mask_components_and_normalized_contours():
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:80, 10:35] = 255
    mask[10:80, 65:90] = 255
    box = contour_box(mask, (0, 0), 100, 100, .9)
    assert len(box['polygons']) == 2
    assert all(0 <= point[key] <= 1 for polygon in box['polygons'] for point in polygon for key in ('x', 'y'))


@pytest.mark.parametrize('legacy_manual', [None, '{"bubbles":[]}', '["old"]', 'broken json'])
def test_external_api_never_queues_cpu_analysis(prepared, monkeypatch, legacy_manual):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from web.backend.database import Base, ComicSeries, ComicIssue, ComicSmartView
    from web.backend import comic_smartview
    from web.backend.routers import comics
    _, copied, _, _ = prepared
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        series = ComicSeries(title='Test', folder_path=str(copied.parent), kind='comic', status='active', detected_at='2026-10-03')
        db.add(series)
        db.flush()
        issue = ComicIssue(series_id=series.id, file_path=str(copied), title='Test', status='active', archive_type='zip', page_count=1, detected_at='2026-10-03')
        db.add(issue)
        db.commit()
        monkeypatch.setattr(comics, '_resolve_issue_path', lambda *_: copied)
        monkeypatch.setattr(comics.smartview_queue, 'enqueue', lambda *_: pytest.fail('External packages must not enqueue inference'))
        _, _, entries, _, signature = comics._smartview_context(db, issue.id, 0)
        legacy = ComicSmartView(issue_id=issue.id, page_index=0, source_signature=signature,
            model_version=comics.current_model_version(), analysis_version=comics.ANALYSIS_VERSION,
            status='queued', manual_json=legacy_manual, result_json=json.dumps({'bubbles': []}))
        db.add(legacy)
        db.commit()
        assert comics.get_issue_manifest(issue.id, 'reader', db)['pages'][0]['smartview_ready']
        response = comics.get_smartview(issue.id, 0, db)
        assert response['source'] == 'external'
        assert response['result']['bubbles']
        assert not response['result'].get('manual_corrections')
        assert comics.smartview_status(issue.id, db)['percent_ready'] == 100
        assert comics.analyze_smartview(issue.id, 0, comics.ComicSmartViewAnalyzeRequest(force=True), db)['queued_pages'] == []
        monkeypatch.setattr('web.backend.database.SessionLocal', sessionmaker(bind=engine))
        monkeypatch.setattr(comic_smartview, 'analyze_page', lambda *_: pytest.fail('A ZIP added after enqueue must skip inference'))
        comic_smartview.SmartViewQueue._analyze(comic_smartview.SmartViewTask(
            issue_id=issue.id, page_index=0, path=str(copied), entry_name=entries[0][0],
            source_signature=signature, direction='ltr', profile='accurate', priority=100))
        payload = comics.correct_smartview(issue.id, 0, comics.ComicSmartViewPatch(bubbles=[]), db)
        assert payload['source'] == 'external'
        assert payload['result']['bubbles'] == []
        assert payload['result']['manual_corrections']
        # Nowy pakiet ma pierwszeństwo także nad korektą poprzedniego pakietu.
        sidecar = package_path(copied)
        manifest = read_manifest(sidecar)
        with zipfile.ZipFile(sidecar) as archive:
            documents = [json.loads(archive.read(page['data'])) for page in manifest['pages']]
        documents[0]['result']['bubbles'][0]['x'] = .3
        write_package(sidecar, manifest, documents)
        payload = comics.get_smartview(issue.id, 0, db)
        assert payload['source'] == 'external'
        assert payload['result']['bubbles'][0]['x'] == .3
        assert not payload['result'].get('manual_corrections')
    engine.dispose()
