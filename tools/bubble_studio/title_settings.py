"""Load the effective settings shown by the per-title settings dialog."""

from pathlib import Path

from .config import series_settings


def load_title_settings(source, input_root):
    """Use the processing root, or the title's parent when outside the queue."""
    source = Path(source).resolve()
    if not source.exists():
        raise ValueError("Wybierz istniejący komiks albo folder jednej serii.")
    input_root = Path(input_root).resolve()
    folder = source if source.is_dir() else source.parent
    outside = folder != input_root and input_root not in folder.parents
    # An external selection must not inherit settings from an unrelated queue.
    # Its own parent is an explicit, bounded root, including the selected folder.
    root = source.parent if outside else input_root
    settings = series_settings(source, root)
    description = "Pokazano ustawienia tytułu z uwzględnieniem folderów nadrzędnych."
    if outside:
        description = (
            "Tytuł poza folderem wejściowym: pokazano ustawienia jego folderu "
            "i wybranego tytułu."
        )
    if settings["layout"] in {"rows", "single"}:
        description += (
            " Obecnie wybrano układ kadrów: "
            + {"rows": "wiersze", "single": "pojedyncza strona"}[settings["layout"]]
            + ". Zapisanie 4koma zastąpi ten wybór automatycznym rozpoznaniem kadrów."
        )
    return dict(
        settings=settings, root=root, outside_input=outside, description=description
    )
