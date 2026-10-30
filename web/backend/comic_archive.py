"""Safe, read-only access to comic archives and image directories."""

from __future__ import annotations

import logging
import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath

logger = logging.getLogger(__name__)

try:
    import rarfile

    _RAR_AVAILABLE = True
except ImportError:
    rarfile = None
    _RAR_AVAILABLE = False


def _configure_rar_backend() -> None:
    """Wskaż `rarfile` rozpakowywacz, gdy nie ma go w PATH.

    CBR to archiwum RAR, więc `rarfile` potrzebuje zewnętrznego narzędzia.
    Domyślnie szuka go wyłącznie w PATH, a typowa instalacja 7-Zipa na Windowsie
    tam nie trafia — biblioteka z plikami CBR nie importowała się wtedy w całości,
    bez żadnej wskazówki dlaczego. Sprawdzamy standardowe lokalizacje i pozwalamy
    nadpisać wybór zmienną środowiskową NOKTURN_SEVENZIP.
    """
    if not _RAR_AVAILABLE:
        return
    if shutil.which(rarfile.UNRAR_TOOL) or shutil.which(rarfile.SEVENZIP_TOOL):
        return
    candidates = [
        os.environ.get("NOKTURN_SEVENZIP"),
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        "/usr/bin/7z",
        "/usr/local/bin/7z",
        "/usr/bin/7zz",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            rarfile.SEVENZIP_TOOL = candidate
            logger.info("CBR: używam rozpakowywacza %s", candidate)
            return
    logger.warning(
        "CBR: brak unrar/7-Zip w PATH — pliki .cbr będą pomijane. "
        "Zainstaluj 7-Zip albo wskaż go zmienną NOKTURN_SEVENZIP.",
    )

try:
    from PIL import Image

    _PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    _PILLOW_AVAILABLE = False


_configure_rar_backend()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
ARCHIVE_EXTENSIONS = {".cbz", ".zip", ".cbr", ".rar"}
MAX_PAGE_BYTES = 80 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 20_000
MAX_COMPRESSION_RATIO = 300


class ComicArchiveError(RuntimeError):
    """Raised when a comic container cannot be read safely."""


@dataclass(frozen=True)
class ComicPage:
    """One validated image entry inside a comic container."""

    name: str
    size: int
    width: int | None = None
    height: int | None = None
    double_page: bool = False


def natural_key(value: str) -> list[object]:
    """Return a stable human-friendly sort key for page and issue names."""
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value)]


def container_type(path: Path) -> str | None:
    """Return the supported storage type for a file or directory."""
    if path.is_dir():
        return "folder"
    if path.suffix.casefold() in {".cbz", ".zip"}:
        return "zip"
    if path.suffix.casefold() in {".cbr", ".rar"}:
        return "rar"
    return None


def _safe_entry_name(raw_name: str) -> str | None:
    name = raw_name.replace("\\", "/")
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts or not pure.name:
        return None
    # macOS packs AppleDouble metadata beside images, often with the same .jpg
    # suffix. These resource forks are not pages and cannot be decoded as one.
    if any(part.casefold() == '__macosx' for part in pure.parts) or pure.name.startswith('._'):
        return None
    return pure.as_posix()


def _validate_size(size: int, compressed_size: int | None = None) -> None:
    if size < 0 or size > MAX_PAGE_BYTES:
        raise ComicArchiveError("Strona przekracza bezpieczny limit 80 MB")
    if compressed_size and compressed_size > 0 and size / compressed_size > MAX_COMPRESSION_RATIO:
        raise ComicArchiveError("Podejrzany współczynnik kompresji strony")


def _list_image_entries_uncached(path: Path) -> list[tuple[str, int]]:
    """List validated image entries without extracting an archive to disk."""
    storage = container_type(path)
    if storage == "folder":
        entries: list[tuple[str, int]] = []
        root = path.resolve()
        for file_path in path.rglob("*"):
            if not file_path.is_file() or file_path.suffix.casefold() not in IMAGE_EXTENSIONS:
                continue
            try:
                relative = file_path.resolve().relative_to(root).as_posix()
                if not _safe_entry_name(relative):
                    continue
                size = file_path.stat().st_size
                _validate_size(size)
            except (OSError, ValueError):
                continue
            entries.append((relative, size))
        return sorted(entries, key=lambda item: natural_key(item[0]))

    if storage == "zip":
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_ARCHIVE_ENTRIES:
                    raise ComicArchiveError("Archiwum zawiera zbyt wiele elementów")
                entries = []
                for info in infos:
                    safe_name = _safe_entry_name(info.filename)
                    if not safe_name or Path(safe_name).suffix.casefold() not in IMAGE_EXTENSIONS:
                        continue
                    _validate_size(info.file_size, info.compress_size)
                    entries.append((safe_name, info.file_size))
                return sorted(entries, key=lambda item: natural_key(item[0]))
        except (OSError, zipfile.BadZipFile) as exc:
            raise ComicArchiveError(f"Nie można odczytać CBZ/ZIP: {exc}") from exc

    if storage == "rar":
        if not _RAR_AVAILABLE:
            raise ComicArchiveError("Obsługa CBR wymaga pakietu rarfile i programu 7-Zip lub bsdtar")
        try:
            with rarfile.RarFile(path) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_ARCHIVE_ENTRIES:
                    raise ComicArchiveError("Archiwum zawiera zbyt wiele elementów")
                entries = []
                for info in infos:
                    safe_name = _safe_entry_name(info.filename)
                    if not safe_name or info.isdir() or Path(safe_name).suffix.casefold() not in IMAGE_EXTENSIONS:
                        continue
                    _validate_size(info.file_size, getattr(info, "compress_size", None))
                    entries.append((safe_name, info.file_size))
                return sorted(entries, key=lambda item: natural_key(item[0]))
        except Exception as exc:
            raise ComicArchiveError(f"Nie można odczytać CBR/RAR: {exc}") from exc

    raise ComicArchiveError("Nieobsługiwany format komiksu")


@lru_cache(maxsize=256)
def _cached_image_entries(path_key: str, mtime_ns: int, size: int) -> tuple[tuple[str, int], ...]:
    """Cache archive indexes; page requests must not rescan a whole container."""
    del mtime_ns, size  # Obie wartości unieważniają klucz po zmianie pliku.
    return tuple(_list_image_entries_uncached(Path(path_key)))


def list_image_entries(path: Path) -> list[tuple[str, int]]:
    """Return a validated, mtime-aware cached page index."""
    # Mtime katalogu nie zmienia się po edycji strony w podfolderze.
    # Indeks katalogu odczytujemy na świeżo, archiwa nadal mają tani cache.
    if path.is_dir():
        return _list_image_entries_uncached(path)
    try:
        stat = path.stat()
    except OSError as exc:
        raise ComicArchiveError(f"Nie można odczytać tomu: {exc}") from exc
    return list(_cached_image_entries(str(path.resolve()), stat.st_mtime_ns, stat.st_size))


def read_entry(path: Path, entry_name: str) -> bytes:
    """Read one already validated entry while keeping the request inside its container."""
    safe_name = _safe_entry_name(entry_name)
    if not safe_name:
        raise ComicArchiveError("Nieprawidłowa ścieżka strony")
    storage = container_type(path)
    if storage == "folder":
        root = path.resolve()
        candidate = (root / Path(*PurePosixPath(safe_name).parts)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ComicArchiveError("Strona znajduje się poza katalogiem tomu") from exc
        if not candidate.is_file() or candidate.suffix.casefold() not in IMAGE_EXTENSIONS:
            raise ComicArchiveError("Strona nie istnieje")
        _validate_size(candidate.stat().st_size)
        return candidate.read_bytes()

    if storage == "zip":
        with zipfile.ZipFile(path) as archive:
            try:
                info = archive.getinfo(safe_name)
            except KeyError as exc:
                raise ComicArchiveError("Strona nie istnieje w archiwum") from exc
            _validate_size(info.file_size, info.compress_size)
            return archive.read(info)

    if storage == "rar" and _RAR_AVAILABLE:
        try:
            with rarfile.RarFile(path) as archive:
                info = archive.getinfo(safe_name)
                _validate_size(info.file_size, getattr(info, "compress_size", None))
                return archive.read(info)
        except Exception as exc:
            raise ComicArchiveError(f"Nie można odczytać strony CBR: {exc}") from exc
    raise ComicArchiveError("Nieobsługiwany format komiksu")


@lru_cache(maxsize=4096)
def image_dimensions(path_key: str, mtime_key: str, entry_name: str) -> tuple[int | None, int | None]:
    """Read image dimensions with an mtime-aware process cache."""
    del mtime_key  # Wartość jest częścią klucza cache i celowo nie jest używana w ciele.
    if not _PILLOW_AVAILABLE:
        return None, None
    try:
        path = Path(path_key)
        safe_name = _safe_entry_name(entry_name)
        if not safe_name:
            return None, None
        storage = container_type(path)
        if storage == "folder":
            root = path.resolve()
            candidate = (root / Path(*PurePosixPath(safe_name).parts)).resolve()
            candidate.relative_to(root)
            with Image.open(candidate) as image:
                return int(image.width), int(image.height)
        if storage == "zip":
            with zipfile.ZipFile(path) as archive, archive.open(safe_name) as stream:
                with Image.open(stream) as image:
                    return int(image.width), int(image.height)
        if storage == "rar" and _RAR_AVAILABLE:
            with rarfile.RarFile(path) as archive, archive.open(safe_name) as stream:
                with Image.open(stream) as image:
                    return int(image.width), int(image.height)
    except Exception:
        pass
    return None, None


def content_type_for(entry_name: str) -> str:
    """Return a conservative media type for a page image."""
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".avif": "image/avif",
    }.get(Path(entry_name).suffix.casefold(), "application/octet-stream")
