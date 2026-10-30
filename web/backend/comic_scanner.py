"""Scanner for folder-grouped comic and manga libraries."""

from __future__ import annotations

import json
import logging
import os
import re
import stat
import threading
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .comic_archive import ARCHIVE_EXTENSIONS, IMAGE_EXTENSIONS, ComicArchiveError, container_type, list_image_entries, natural_key
from .comic_bubble_package import is_bubble_package

logger = logging.getLogger(__name__)
_scan_lock = threading.Lock()


def is_yacreader_path(path) -> bool:
    """Recognize cache paths using either separator, without touching storage."""
    return ".yacreaderlibrary" in str(path).replace("\\", "/").casefold().split("/")


def exclude_legacy_yacreader_records(db) -> int:
    """Hide previously indexed cache records, retaining IDs and user relations."""
    from sqlalchemy import text
    condition = "instr('/' || lower(replace({column}, char(92), '/')) || '/', '/.yacreaderlibrary/') > 0"
    series = db.execute(text("UPDATE comic_series SET status='ignored' WHERE status!='ignored' AND "
                             + condition.format(column="folder_path"))).rowcount
    issues = db.execute(text("UPDATE comic_issues SET status='ignored' WHERE status!='ignored' AND ("
                             + condition.format(column="file_path")
                             + " OR series_id IN (SELECT id FROM comic_series WHERE status='ignored'))")).rowcount
    db.commit()
    return series + issues


def _raise_walk_error(error):
    raise error

try:
    import rarfile
except ImportError:
    rarfile = None


def get_graphic_dirs(db, UserSettings, kind: str) -> list[str]:
    """Return configured roots for comics or manga."""
    key = "manga_dirs" if kind == "manga" else "comic_dirs"
    from .settings_service import SystemSetting, ensure_settings_tables

    ensure_settings_tables(db)
    system_setting = db.get(SystemSetting, key)
    raw_value = system_setting.value_json if system_setting else None
    if raw_value is None:
        setting = db.query(UserSettings).filter(UserSettings.key == key).first()
        raw_value = setting.value if setting else None
    if not raw_value:
        return []
    try:
        values = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return []
    return [value for value in values if isinstance(value, str) and value.strip()] if isinstance(values, list) else []


def _read_comicinfo(path: Path) -> dict[str, str]:
    """Read basic ComicInfo.xml metadata without extracting the archive."""
    raw: bytes | None = None
    storage = container_type(path)
    try:
        if storage == "folder":
            info_path = next((entry for entry in path.iterdir() if entry.is_file() and entry.name.casefold() == "comicinfo.xml"), None)
            raw = info_path.read_bytes() if info_path else None
        elif storage == "zip":
            with zipfile.ZipFile(path) as archive:
                name = next((name for name in archive.namelist() if Path(name).name.casefold() == "comicinfo.xml"), None)
                raw = archive.read(name) if name else None
        elif storage == "rar" and rarfile is not None:
            with rarfile.RarFile(path) as archive:
                name = next((name for name in archive.namelist() if Path(name).name.casefold() == "comicinfo.xml"), None)
                raw = archive.read(name) if name else None
    except Exception as exc:
        logger.debug("ComicInfo unavailable for %s: %s", path, exc)
    if not raw or len(raw) > 2 * 1024 * 1024:
        return {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return {}
    values = {}
    for key in (
        "Title", "Series", "Number", "Volume", "Summary", "Year", "Publisher",
        "Writer", "Penciller", "Inker", "Colorist", "Letterer", "CoverArtist",
        "Genre", "Tags", "LanguageISO", "AgeRating", "Manga", "Characters",
        "Teams", "Locations", "StoryArc",
    ):
        node = root.find(key)
        if node is not None and node.text:
            values[key.casefold()] = node.text.strip()
    # ComicInfo pozwala jawnie wskazać okładkę i rozkładówki.
    cover_index = None
    double_indexes: list[int] = []
    pages = root.find("Pages")
    if pages is not None:
        for page in pages.findall("Page"):
            try:
                index = int(page.attrib.get("Image", "-1"))
            except ValueError:
                continue
            page_type = page.attrib.get("Type", "").casefold()
            if page_type == "frontcover":
                cover_index = index
            elif page_type == "doublepage":
                double_indexes.append(index)
    if cover_index is not None:
        values["cover_index"] = str(cover_index)
    if double_indexes:
        values["double_indexes"] = ",".join(str(value) for value in double_indexes)
    return values


def _parse_number(name: str, metadata: dict[str, str]) -> tuple[float | None, str | None]:
    raw = metadata.get("number") or metadata.get("volume")
    if not raw:
        match = re.search(r"(?:^|[\s#._-])(?:tom|vol(?:ume)?|t)?\s*#?\s*(\d+(?:[.,]\d+)?)", name, re.IGNORECASE)
        raw = match.group(1) if match else None
    if not raw:
        return None, None
    normalized = raw.replace(",", ".")
    try:
        return float(normalized), raw
    except ValueError:
        return None, raw


def _issue_candidates(series_folder: Path) -> list[Path]:
    if is_yacreader_path(series_folder) or is_bubble_package(series_folder):
        return []
    archives: list[Path] = []
    image_dirs: list[Path] = []
    # Nie wchodzimy w cache YACReadera, zamiast filtrować dopiero po kosztownym rglob.
    for directory, children, filenames in os.walk(series_folder, onerror=_raise_walk_error):
        children[:] = [name for name in children if name.casefold() != ".yacreaderlibrary" and not is_bubble_package(Path(name))]
        folder = Path(directory)
        archives.extend(folder / name for name in filenames if Path(name).suffix.casefold() in ARCHIVE_EXTENSIONS and not is_bubble_package(Path(name)))
        if any(Path(name).suffix.casefold() in IMAGE_EXTENSIONS for name in filenames):
            image_dirs.append(folder)
    archives.sort(key=lambda path: natural_key(str(path.relative_to(series_folder))))
    image_dirs.sort(key=lambda path: natural_key(str(path)))
    return archives + [folder for folder in image_dirs if not any(folder in archive.parents for archive in archives)]


def _series_folders(root: Path) -> list[Path]:
    if is_yacreader_path(root) or is_bubble_package(root):
        return []
    entries = [(path, path.stat().st_mode) for path in root.iterdir() if path.name.casefold() != ".yacreaderlibrary" and not is_bubble_package(path)]
    children = sorted([path for path, mode in entries if stat.S_ISDIR(mode)], key=lambda path: natural_key(path.name))
    direct_archives = any(stat.S_ISREG(mode) and path.suffix.casefold() in ARCHIVE_EXTENSIONS for path, mode in entries)
    direct_images = any(stat.S_ISREG(mode) and path.suffix.casefold() in IMAGE_EXTENSIONS for path, mode in entries)
    return ([root] if direct_archives or direct_images else []) + children


def run_comic_scan(progress_callback=None, roots_filter: set[str] | None = None) -> dict:
    """Serialize scans to avoid racing manual and automatic reconciliation."""
    with _scan_lock:
        return _run_comic_scan(progress_callback, roots_filter)


def _run_comic_scan(progress_callback=None, roots_filter: set[str] | None = None) -> dict:
    """Scan comic and manga roots and upsert series/issues in short transactions."""
    from .database import ComicIssue, ComicSeries, SessionLocal
    from .routers.user import UserSettings

    stats = {"series_found": 0, "issues_found": 0, "pages_found": 0, "missing": 0, "errors": 0}
    db = SessionLocal()
    seen_series: set[str] = set()
    seen_issues: set[str] = set()
    readable_roots: set[Path] = set()
    failed_folders: set[Path] = set()
    now = datetime.now(timezone.utc).isoformat()
    try:
        stats["ignored"] = exclude_legacy_yacreader_records(db)
        roots = [(kind, raw) for kind in ("comic", "manga") for raw in get_graphic_dirs(db, UserSettings, kind)]
        candidates: list[tuple[str, Path]] = []
        for kind, raw_root in roots:
            root = Path(raw_root)
            if roots_filter is not None and str(root.resolve()) not in roots_filter:
                continue
            try:
                from .disk_io import retry_storage_read
                candidates.extend((kind, folder) for folder in retry_storage_read(lambda: _series_folders(root), root))
                readable_roots.add(root.resolve())
            except OSError as exc:
                logger.warning("Nie można odczytać katalogu %s: %s", raw_root, exc)
                stats["errors"] += 1

        for processed, (kind, folder) in enumerate(candidates, start=1):
            folder_key = str(folder.resolve())
            seen_series.add(folder_key)
            series = db.query(ComicSeries).filter(ComicSeries.folder_path == folder_key).first()
            if series is None:
                series = ComicSeries(folder_path=folder_key, title=folder.name, kind=kind, detected_at=now)
                db.add(series)
                db.flush()
            else:
                series.title = folder.name
                series.kind = kind
                series.status = "active"
            # Odczyt archiwów nie trzyma rezerwacji zapisu SQLite.
            db.commit()

            issue_count = 0
            try:
                issue_paths = _issue_candidates(folder)
            except OSError as exc:
                logger.warning("Nie można przeskanować serii %s: %s", folder, exc)
                stats["errors"] += 1
                failed_folders.add(folder.resolve())
                issue_paths = []
            for issue_path in issue_paths:
                path_key = str(issue_path.resolve())
                seen_issues.add(path_key)
                try:
                    entries = list_image_entries(issue_path)
                    if not entries:
                        continue
                    metadata = _read_comicinfo(issue_path)
                    stat = issue_path.stat()
                except (ComicArchiveError, OSError) as exc:
                    logger.warning("Pominięto %s: %s", issue_path, exc)
                    stats["errors"] += 1
                    failed_folders.add(folder.resolve())
                    continue
                number, number_raw = _parse_number(issue_path.stem if issue_path.is_file() else issue_path.name, metadata)
                cover_index = int(metadata.get("cover_index", "0")) if metadata.get("cover_index", "0").isdigit() else 0
                cover_index = min(max(cover_index, 0), len(entries) - 1)
                issue = db.query(ComicIssue).filter(ComicIssue.file_path == path_key).first()
                values = {
                    "series_id": series.id,
                    "title": metadata.get("title") or (issue_path.stem if issue_path.is_file() else issue_path.name),
                    "number": number,
                    "number_raw": number_raw,
                    "archive_type": container_type(issue_path),
                    "page_count": len(entries),
                    "cover_entry": entries[cover_index][0],
                    "metadata_json": json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
                    "file_size_bytes": stat.st_size if issue_path.is_file() else sum(size for _, size in entries),
                    "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "status": "active",
                }
                if issue is None:
                    issue = ComicIssue(file_path=path_key, detected_at=now, **values)
                    db.add(issue)
                else:
                    for key, value in values.items():
                        setattr(issue, key, value)
                issue_count += 1
                stats["issues_found"] += 1
                stats["pages_found"] += len(entries)
                db.commit()
            if folder.resolve() not in failed_folders:
                series.issue_count = issue_count
            stats["series_found"] += 1
            db.commit()
            if progress_callback:
                progress_callback(processed, len(candidates), dict(stats))

        def safely_absent(path_key, seen):
            path = Path(path_key)
            return (path_key not in seen
                    and any(path.is_relative_to(root) for root in readable_roots)
                    and not any(path.is_relative_to(folder) for folder in failed_folders))

        for series in db.query(ComicSeries).filter(ComicSeries.status == "active").all():
            if safely_absent(series.folder_path, seen_series):
                series.status = "missing"
                stats["missing"] += 1
        for issue in db.query(ComicIssue).filter(ComicIssue.status == "active").all():
            if safely_absent(issue.file_path, seen_issues):
                issue.status = "missing"
                stats["missing"] += 1
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Błąd skanowania komiksów i mang")
        stats["errors"] += 1
    finally:
        db.close()
    return stats
