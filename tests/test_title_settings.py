import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.bubble_studio.config import save_reading_mode, series_settings
from tools.bubble_studio.title_settings import load_title_settings


def write_settings(folder, **values):
    (folder / "bubble-studio.json").write_text(json.dumps(values), encoding="utf8")


def test_direction_only_change_preserves_inherited_4koma(tmp_path):
    root = tmp_path / "input"
    folder = root / "series"
    folder.mkdir(parents=True)
    a, b = folder / "a.cbz", folder / "b.cbz"
    a.touch()
    b.touch()
    write_settings(folder, reading_mode="four_panel_strips", direction="rtl")
    loaded = load_title_settings(a, root)
    assert loaded["settings"]["reading_mode"] == "four_panel_strips"
    assert loaded["settings"]["direction"] == "rtl"
    save_reading_mode(a, loaded["settings"]["reading_mode"], "ltr")
    assert series_settings(a, root)["reading_mode"] == "four_panel_strips"
    assert series_settings(a, root)["direction"] == "ltr"
    assert series_settings(b, root)["reading_mode"] == "four_panel_strips"
    assert series_settings(b, root)["direction"] == "rtl"


def test_title_override_beats_root_and_intermediate_folder(tmp_path):
    root = tmp_path / "input"
    folder = root / "series" / "volumes"
    folder.mkdir(parents=True)
    source = folder / "a.cbz"
    source.touch()
    write_settings(
        root, reading_mode="four_panel_strips", direction="ltr", quality="fast"
    )
    write_settings(folder.parent, direction="rtl")
    save_reading_mode(source, "auto")
    loaded = load_title_settings(source, root)
    assert loaded["settings"] == series_settings(source, root)
    assert loaded["settings"]["reading_mode"] == "auto"
    assert loaded["settings"]["direction"] == "rtl"
    assert loaded["settings"]["quality"] == "fast"
    assert loaded["root"] == root
    assert not loaded["outside_input"]


@pytest.mark.parametrize("folder_selection", [False, True])
def test_external_title_uses_its_own_parent_without_unrelated_input_settings(
    tmp_path, folder_selection
):
    root = tmp_path / "input"
    root.mkdir()
    write_settings(root, reading_mode="auto", direction="ltr")
    external = tmp_path / "external"
    external.mkdir()
    write_settings(external, reading_mode="four_panel_strips", direction="rtl")
    source = external / ("Series" if folder_selection else "book.cbz")
    source.mkdir() if folder_selection else source.touch()
    loaded = load_title_settings(source, root)
    assert loaded["root"] == external
    assert loaded["outside_input"]
    assert loaded["settings"]["reading_mode"] == "four_panel_strips"
    assert loaded["settings"]["direction"] == "rtl"
    assert "poza folderem" in loaded["description"]


@pytest.mark.parametrize("values", [[], None, {"reading_mode": []}, {"unknown": True}])
def test_invalid_parent_configuration_is_rejected_without_writing(tmp_path, values):
    folder = tmp_path / "series"
    folder.mkdir()
    source = folder / "book.cbz"
    source.touch()
    settings = tmp_path / "bubble-studio.json"
    settings.write_text(json.dumps(values), encoding="utf8")
    before = settings.read_bytes()
    with pytest.raises(ValueError):
        load_title_settings(source, tmp_path)
    assert settings.read_bytes() == before
    assert not source.with_name(source.name + ".bubble-studio.json").exists()


def test_existing_explicit_frame_layout_is_visible_in_description(tmp_path):
    source = tmp_path / "book.cbz"
    source.touch()
    write_settings(tmp_path, layout="rows")
    loaded = load_title_settings(source, tmp_path)
    assert loaded["settings"]["layout"] == "rows"
    assert "wiersze" in loaded["description"]
    assert "Zapisanie 4koma" in loaded["description"]


def test_missing_selection_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_title_settings(tmp_path / "missing.cbz", tmp_path)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Tk dialog")
def test_real_dialog_keeps_inherited_mode_when_only_direction_is_changed(tmp_path):
    root = tmp_path / "input"
    folder = root / "series"
    folder.mkdir(parents=True)
    source = folder / "book.cbz"
    source.touch()
    write_settings(folder, reading_mode="four_panel_strips", direction="rtl")
    script = r"""
import sys
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
from tools.bubble_studio.gui import Studio
from tools.bubble_studio.config import series_settings
from pathlib import Path
root = tk.Tk()
try:
    studio = Studio(root)
    studio.input.set(sys.argv[1])
    window = studio.reading_settings()
    root.update()
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    with patch('tools.bubble_studio.gui.filedialog.askopenfilename', return_value=sys.argv[2]):
        next(w for w in descendants(window) if isinstance(w, ttk.Button) and w.cget('text') == 'Wybierz komiks…').invoke()
    root.update()
    combos = [w for w in descendants(window) if isinstance(w, ttk.Combobox)]
    assert combos[0].get().startswith('4koma'), combos[0].get()
    assert combos[1].get() == 'Od prawej do lewej (manga)', combos[1].get()
    combos[1].set('Od lewej do prawej')
    next(w for w in descendants(window) if isinstance(w, ttk.Button) and w.cget('text') == 'Zapisz ustawienia tytułu').invoke()
    settings = series_settings(Path(sys.argv[2]), Path(sys.argv[1]))
    assert settings['reading_mode'] == 'four_panel_strips'
    assert settings['direction'] == 'ltr'
finally:
    root.destroy()
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-c", script, str(root), str(source)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf8",
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
