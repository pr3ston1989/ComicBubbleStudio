import copy
import hashlib
import io
import zipfile

import pytest

from tools.bubble_studio.package_audit import encode, read_document, write_document
from web.backend.comic_bubble_package import (
    BubblePackageError,
    MAX_PAGE_JSON_BYTES,
    _json,
)


def document(large=False):
    d = dict(
        result=dict(width=100, height=100, direction="rtl", panels=[], bubbles=[]),
        review=dict(verified=True, flags=[]),
        analysis=dict(
            pipeline="test",
            reading_anchors={},
            text_check=dict(regions=[]),
            tail_tips=dict(regions=[]),
        ),
    )
    if large:
        d["analysis"]["original"] = dict(
            history="".join(
                hashlib.sha256(str(i).encode()).hexdigest() for i in range(40000)
            )
        )
    return d


@pytest.mark.parametrize("large", [False, True])
def test_reader_page_stays_bounded_and_studio_restores_exact_audit(large):
    d = document(large)
    before = copy.deepcopy(d)
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as archive:
        write_document(archive, "pages/00000.json", d)
    assert d == before
    with zipfile.ZipFile(buff) as archive:
        assert archive.getinfo("pages/00000.json").file_size <= MAX_PAGE_JSON_BYTES
        reader = _json(archive, "pages/00000.json", MAX_PAGE_JSON_BYTES)
        assert reader["result"] == d["result"] and reader["review"] == d["review"]
        assert read_document(archive, "pages/00000.json") == d
        assert ("studio/pages/00000.json" in archive.namelist()) is large


@pytest.mark.parametrize("corruption", ["path", "hash", "result", "missing"])
def test_corrupt_or_redirected_audit_is_rejected(corruption):
    full = document()
    raw = encode(full)
    small = copy.deepcopy(full)
    small["studio_document"] = dict(
        path="studio/pages/00000.json", sha256=hashlib.sha256(raw).hexdigest()
    )
    if corruption == "path":
        small["studio_document"]["path"] = "../private.json"
    if corruption == "hash":
        small["studio_document"]["sha256"] = "0" * 64
    if corruption == "result":
        small["result"]["width"] = 200
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("pages/00000.json", encode(small))
        if corruption != "missing":
            archive.writestr("studio/pages/00000.json", raw)
    with zipfile.ZipFile(buff) as archive:
        with pytest.raises(BubblePackageError):
            read_document(archive, "pages/00000.json")


def test_actual_reading_geometry_cannot_be_dropped_to_fit():
    d = document()
    d["result"]["huge"] = "x" * (2 * MAX_PAGE_JSON_BYTES)
    before = copy.deepcopy(d)
    with zipfile.ZipFile(io.BytesIO(), "w") as archive:
        with pytest.raises(BubblePackageError):
            write_document(archive, "pages/00000.json", d)
    assert d == before
