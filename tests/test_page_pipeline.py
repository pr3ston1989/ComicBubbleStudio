import io
import json
import zipfile
from pathlib import Path
from threading import Event

import pytest
from PIL import Image

from tools.bubble_studio import runner
from web.backend.comic_bubble_package import load_package


def make_book(tmp_path):
    source = tmp_path / "book.cbz"
    with zipfile.ZipFile(source, "w") as archive:
        for number in (2, 1):
            data = io.BytesIO()
            Image.new("RGB", (20, 20), (number, 0, 0)).save(data, "PNG")
            archive.writestr(f"{number}.png", data.getvalue())
    return source


class OverlappingAnalyzer:
    def __init__(self, fail_second=False):
        self.first_started = Event()
        self.second_started = Event()
        self.fail_second = fail_second

    def analyze(self, image, **options):
        return self.document(image)

    def start_page(self, image, *, finish_later, **options):
        if image.getpixel((0, 0))[0] == 1:
            return finish_later(self.finish_first, image)
        assert self.first_started.wait(5)
        self.second_started.set()
        if self.fail_second:
            raise RuntimeError("page two failed")
        return self.document(image)

    def finish_first(self, image):
        self.first_started.set()
        assert self.second_started.wait(5)
        return self.document(image)

    @staticmethod
    def document(image):
        return {
            "result": dict(width=image.width, height=image.height,
                           direction="ltr", layout="auto", panels=[], bubbles=[], confidence=0),
            "analysis": {"marker": image.getpixel((0, 0))[0]},
            "review": {"flags": [], "verified": False},
        }


def test_completed_pages_are_published_in_source_order(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.os, "cpu_count", lambda: 8)
    source = make_book(tmp_path)
    output = tmp_path / "output"
    runner.process_comic(source, Path(source.name), output, tmp_path / "work",
                         OverlappingAnalyzer())
    package = load_package(output / source.name)
    assert [row["name"] for row in package.manifest["pages"]] == ["1.png", "2.png"]
    with zipfile.ZipFile(package.sidecar) as archive:
        assert [json.loads(archive.read(row["data"]))["analysis"]["marker"]
                for row in package.manifest["pages"]] == [1, 2]


def test_finished_page_checkpoint_survives_failure_on_next_page(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.os, "cpu_count", lambda: 8)
    source = make_book(tmp_path)
    output, work = tmp_path / "output", tmp_path / "work"
    with pytest.raises(RuntimeError, match="page two failed"):
        runner.process_comic(source, Path(source.name), output, work,
                             OverlappingAnalyzer(fail_second=True))
    first, = work.glob("*/00000.json")
    assert json.loads(first.read_text(encoding="utf8"))["document"]["analysis"]["marker"] == 1
    assert not (output / source.name).exists()
    model = OverlappingAnalyzer()
    seen = []
    def analyze(image, **options):
        seen.append(image.getpixel((0, 0))[0])
        return model.document(image)
    model.analyze = analyze
    runner.process_comic(source, Path(source.name), output, work, model,
                         parallel_pages=False)
    assert seen == [2]
