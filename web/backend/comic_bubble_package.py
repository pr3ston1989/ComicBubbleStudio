"""Portable, bounded Bubble Studio packages; no inference or database dependencies."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import zipfile
from functools import lru_cache
from pathlib import Path, PurePosixPath

from .comic_archive import list_image_entries, read_entry

logger = logging.getLogger(__name__)
PACKAGE_SUFFIX = ".nokturn-bubbles.zip"
PACKAGE_VERSION = 1
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_PAGE_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKAGE_BYTES = 1024 * 1024 * 1024
MAX_PACKAGE_ENTRIES = 20_000
MAX_UNPACKED_BYTES = 512 * 1024 * 1024
MAX_POINTS_PER_PAGE = 32_000


class BubblePackageError(ValueError):
    """A package is malformed, unsafe, or belongs to a different edition."""


def package_path(source: Path) -> Path:
    """Keep the complete filename, avoiding collisions between CBZ and CBR editions."""
    return source / PACKAGE_SUFFIX if source.is_dir() else Path(str(source) + PACKAGE_SUFFIX)


def is_bubble_package(path: Path) -> bool:
    """Exclude sidecars and review output from comic scanning."""
    return path.name.casefold().endswith(PACKAGE_SUFFIX) or any(
        part.casefold() == ".nokturn-bubble-review" for part in path.parts
    )


def file_sha256(path: Path) -> str:
    """Hash incrementally rather than loading an entire comic into RAM."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256(source: Path, pages: list[dict] | None = None) -> str:
    """Hash archive bytes, or ordered names and page hashes for an image directory."""
    if source.is_file():
        return file_sha256(source)
    pages = pages if pages is not None else [
        {"name": name, "sha256": hashlib.sha256(read_entry(source, name)).hexdigest()}
        for name, _ in list_image_entries(source)
    ]
    digest = hashlib.sha256()
    for page in pages:
        digest.update(f'{page["name"]}\0{page["sha256"]}\n'.encode("utf-8"))
    return digest.hexdigest()


def _finite(value, minimum=0.0, maximum=1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise BubblePackageError("Współrzędna nie jest liczbą")
    value = float(value)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise BubblePackageError("Współrzędna poza dopuszczalnym zakresem")
    return value


def _rectangle(item: dict) -> dict:
    result = {key: _finite(item.get(key)) for key in ("x", "y", "w", "h")}
    if result["w"] <= 0 or result["h"] <= 0 or result["x"] + result["w"] > 1.000001 or result["y"] + result["h"] > 1.000001:
        raise BubblePackageError("Obszar wychodzi poza stronę")
    return result



def _tail_tip(item, box, width, height):
    """Ignore invalid optional metadata without rejecting readable geometry."""
    raw = item.get("tail_tip")
    polygons = box.get("polygons", [])
    if (not isinstance(raw, dict) or raw.get("kind") != "visible-outline"
            or box.get("type") != "bubble" or item.get("group") or len(polygons) != 1):
        return None
    try:
        x, y, confidence = (_finite(raw.get(k)) for k in ("x", "y", "confidence"))
    except BubblePackageError:
        return None
    if confidence < .9 or not (box["x"] <= x <= box["x"] + box["w"]
                              and box["y"] <= y <= box["y"] + box["h"]):
        return None
    if not any(math.hypot((box["x"] + p["x"] * box["w"] - x) * width,
                          (box["y"] + p["y"] * box["h"] - y) * height) <= 2
               for p in polygons[0]):
        return None
    return dict(x=x, y=y, confidence=confidence, kind="visible-outline")


def validate_result(raw: dict) -> dict:
    """Whitelist geometry and bound contour complexity before exposing it to SVG."""
    if not isinstance(raw, dict):
        raise BubblePackageError("Brak geometrii strony")
    width, height = raw.get("width"), raw.get("height")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100_000 for value in (width, height)):
        raise BubblePackageError("Nieprawidłowe wymiary strony")
    if width * height > 120_000_000 or raw.get("direction") not in {"ltr", "rtl"}:
        raise BubblePackageError("Nieprawidłowa strona lub kierunek czytania")
    points_left = MAX_POINTS_PER_PAGE

    def outlines(item):
        nonlocal points_left
        polygons = item.get("polygons", [item["polygon"]] if item.get("polygon") else [])
        if not isinstance(polygons, list) or len(polygons) > 16:
            raise BubblePackageError("Zbyt wiele konturów")
        result = []
        for polygon in polygons:
            if not isinstance(polygon, list) or not 3 <= len(polygon) <= 2048:
                raise BubblePackageError("Nieprawidłowy kontur")
            points_left -= len(polygon)
            if points_left < 0:
                raise BubblePackageError("Zbyt złożona geometria strony")
            if any(not isinstance(point, dict) for point in polygon):
                raise BubblePackageError("Nieprawidłowy punkt konturu")
            result.append([{"x": _finite(point.get("x")), "y": _finite(point.get("y"))} for point in polygon])
        return {"polygons": result, "polygon": result[0]} if result else {}

    collections = {}
    for name, prefix, limit in (("panels", "p", 64), ("bubbles", "b", 128)):
        items = raw.get(name)
        if not isinstance(items, list) or len(items) > limit:
            raise BubblePackageError("Zbyt wiele obszarów")
        normalized, identifiers = [], set()
        for index, item in enumerate(items, 1):
            if not isinstance(item, dict):
                raise BubblePackageError("Nieprawidłowy obszar")
            identifier = item.get("id")
            if not isinstance(identifier, str) or not re.fullmatch(prefix + r"\d{1,5}", identifier) or identifier in identifiers:
                raise BubblePackageError("Nieprawidłowy identyfikator obszaru")
            identifiers.add(identifier)
            box = {**_rectangle(item), "id": identifier, "order": index,
                   "confidence": _finite(item.get("confidence", 0)), **outlines(item)}
            if name == "bubbles":
                box["type"] = "text" if item.get("type") == "text" else "bubble"
                box["panel_id"] = item.get("panel_id") if item.get("panel_id") in {panel["id"] for panel in collections["panels"]} else None
                box["source"] = "external"
                if item.get("polarity") in {"light", "dark"}:
                    box["polarity"] = item["polarity"]
                if item.get("group"):
                    box["group"] = {**_rectangle(item["group"]), **outlines(item["group"])}
                tip = _tail_tip(item, box, width, height)
                if tip is not None:
                    box["tail_tip"] = tip
            normalized.append(box)
        collections[name] = normalized
    return {
        "version": PACKAGE_VERSION, "model_version": "bubble-studio-1", "profile": "accurate",
        "width": width, "height": height, "direction": raw["direction"],
        "layout": raw.get("layout") if raw.get("layout") in {"auto", "rows", "columns", "single"} else "auto",
        "crop": _rectangle(raw.get("crop", {"x": 0, "y": 0, "w": 1, "h": 1})),
        "confidence": _finite(raw.get("confidence", 0)), "detector": "external", **collections,
    }


def _json(archive: zipfile.ZipFile, name: str, limit: int) -> dict:
    try:
        info = archive.getinfo(name)
        if info.file_size > limit or info.file_size / max(info.compress_size, 1) > 1000:
            raise BubblePackageError("Przekroczony rozmiar danych pakietu")
        result = json.loads(archive.read(info))
        if not isinstance(result, dict):
            raise BubblePackageError("Nieprawidłowy dokument JSON")
        return result
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BubblePackageError("Brak lub uszkodzony dokument pakietu") from exc


def read_manifest(sidecar: Path) -> dict:
    """Inspect the ZIP without extracting any member or trusting embedded paths."""
    if sidecar.stat().st_size > MAX_PACKAGE_BYTES:
        raise BubblePackageError("Pakiet jest zbyt duży")
    with zipfile.ZipFile(sidecar) as archive:
        infos = archive.infolist()
        names = {info.filename for info in infos}
        if len(infos) > MAX_PACKAGE_ENTRIES or len(names) != len(infos) or sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
            raise BubblePackageError("Zbyt wiele lub powtórzone elementy pakietu")
        for info in infos:
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts or "\\" in info.filename or ":" in info.filename or info.flag_bits & 1:
                raise BubblePackageError("Niebezpieczny element pakietu")
        manifest = _json(archive, "manifest.json", MAX_MANIFEST_BYTES)
        pages = manifest.get("pages")
        source = manifest.get("source", {})
        if manifest.get("format") != "nokturn-bubbles" or manifest.get("version") != PACKAGE_VERSION:
            raise BubblePackageError("Nieobsługiwana wersja pakietu")
        if not isinstance(source, dict) or not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", ""))):
            raise BubblePackageError("Brak sumy kontrolnej komiksu")
        if not isinstance(pages, list) or not 1 <= len(pages) <= 20_000:
            raise BubblePackageError("Nieprawidłowy spis stron")
        for index, page in enumerate(pages):
            if not isinstance(page, dict) or page.get("index") != index or page.get("data") != f"pages/{index:05}.json":
                raise BubblePackageError("Nieprawidłowy indeks strony")
            name = PurePosixPath(str(page.get("name", "")))
            if not name.parts or name.is_absolute() or ".." in name.parts or "\\" in str(name) or ":" in str(name):
                raise BubblePackageError("Niebezpieczna nazwa strony")
            if not re.fullmatch(r"[a-f0-9]{64}", str(page.get("sha256", ""))) or type(page.get("size")) is not int or page["size"] < 1:
                raise BubblePackageError("Nieprawidłowa tożsamość strony")
            document = _json(archive, page["data"], MAX_PAGE_JSON_BYTES)
            validate_result(document.get("result"))
            review = document.get("review", {})
            page["review_required"] = bool(review.get("flags")) and review.get("verified") is not True if isinstance(review, dict) else False
        return manifest


class BubblePackage:
    """A verified sidecar tied to one exact source edition."""

    def __init__(self, source: Path, sidecar: Path, manifest: dict):
        self.source, self.sidecar, self.manifest = source, sidecar, manifest
        self.invalid = False

    def page(self, index: int) -> dict:
        """Validate per-page geometry and byte identity before use in the reader."""
        descriptor = self.manifest["pages"][index]
        data = read_entry(self.source, descriptor["name"])
        if hashlib.sha256(data).hexdigest() != descriptor["sha256"]:
            self.invalid = True
            raise BubblePackageError("Strona nie pasuje do przygotowanego pakietu")
        with zipfile.ZipFile(self.sidecar) as archive:
            page = _json(archive, descriptor["data"], MAX_PAGE_JSON_BYTES)
        result = validate_result(page.get("result"))
        review = page.get("review") if isinstance(page.get("review"), dict) else {}
        flags = review.get("flags") if isinstance(review.get("flags"), list) else []
        return {"status": "ready", "source": "external", "model_version": "bubble-studio-1",
                "analysis_version": PACKAGE_VERSION, "profile": "accurate", "result": result,
                "confidence": result["confidence"], "review_required": bool(flags) and review.get("verified") is not True,
                "review_flags": [str(flag)[:200] for flag in flags[:30]], "verified": review.get("verified") is True}


@lru_cache(maxsize=16)
def _load_cached(source_name: str, sidecar_name: str, identity: tuple) -> BubblePackage | None:
    del identity  # Zmiany źródła/pakietu zmieniają klucz, nie ufamy zapisanej dacie utworzenia.
    source, sidecar = Path(source_name), Path(sidecar_name)
    try:
        manifest = read_manifest(sidecar)
        entries = list_image_entries(source)
        if [(page["name"], page["size"]) for page in manifest["pages"]] != entries:
            raise BubblePackageError("Pakiet pochodzi z innego wydania / spisu stron")
        if source_sha256(source) != manifest["source"]["sha256"]:
            raise BubblePackageError("Pakiet pochodzi z innego wydania / zawartości komiksu")
        return BubblePackage(source, sidecar, manifest)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, TypeError, AttributeError) as exc:
        logger.warning("Bubble Studio: pomijam pakiet %s: %s", sidecar.name, exc)
        return None


def load_package(source: Path) -> BubblePackage | None:
    """Discover sidecars automatically; absence or corruption preserves legacy SmartView."""
    sidecar = package_path(source)
    try:
        if not sidecar.is_file():
            return None
        stat, package_stat = source.stat(), sidecar.stat()
        identity = (stat.st_size, stat.st_mtime_ns, package_stat.st_size, package_stat.st_mtime_ns)
        if source.is_dir():
            identity += tuple((name, size, (source / name).stat().st_mtime_ns) for name, size in list_image_entries(source))
        package = _load_cached(str(source.resolve()), str(sidecar.resolve()), identity)
        return package if package and not package.invalid else None
    except (OSError, RuntimeError):
        return None
