"""Keep large Studio audits while preserving Nokturn's bounded page format."""

import copy
import hashlib
import json

from web.backend.comic_bubble_package import (
    BubblePackageError,
    MAX_PAGE_JSON_BYTES,
    _json,
)

MAX_STUDIO_DOCUMENT_BYTES = 16 * 1024 * 1024


def encode(document):
    return json.dumps(document, ensure_ascii=False, allow_nan=False).encode("utf8")


def write_document(archive, name, document):
    raw = encode(document)
    if len(raw) <= MAX_PAGE_JSON_BYTES:
        archive.writestr(name, raw)
        return
    if len(raw) > MAX_STUDIO_DOCUMENT_BYTES:
        raise BubblePackageError("Dokument kontroli Studio przekracza 16 MB")
    # The reader needs result geometry; Studio retains the complete audit and
    # reversible snapshots in an integrity-checked, optional package member.
    small = copy.deepcopy(document)
    full_name = "studio/" + name
    small["analysis"] = {
        k: document.get("analysis", {})[k]
        for k in (
            "pipeline",
            "quality",
            "reading_mode",
            "reading_anchors",
            "text_check",
            "tail_tips",
        )
        if k in document.get("analysis", {})
    }
    small["studio_document"] = dict(
        path=full_name, sha256=hashlib.sha256(raw).hexdigest()
    )
    encoded = encode(small)
    if len(encoded) > MAX_PAGE_JSON_BYTES:
        raise BubblePackageError("Geometria strony przekracza limit czytnika")
    archive.writestr(name, encoded)
    archive.writestr(full_name, raw)


def read_document(archive, name):
    small = _json(archive, name, MAX_PAGE_JSON_BYTES)
    attachment = small.get("studio_document")
    if attachment is None:
        return small
    if (
        not isinstance(attachment, dict)
        or attachment.get("path") != "studio/" + name
        or not isinstance(attachment.get("sha256"), str)
    ):
        raise BubblePackageError("Nieprawidłowe dane kontroli Studio")
    full_name = attachment["path"]
    document = _json(archive, full_name, MAX_STUDIO_DOCUMENT_BYTES)
    if hashlib.sha256(archive.read(full_name)).hexdigest() != attachment["sha256"]:
        raise BubblePackageError("Niezgodna suma kontrolna dokumentu Studio")
    if document.get("result") != small.get("result") or document.get(
        "review"
    ) != small.get("review"):
        raise BubblePackageError("Niezgodny wynik dokumentu Studio")
    return document
