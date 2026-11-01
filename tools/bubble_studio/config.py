"""Strict, inherited per-series settings without executable configuration."""

import json
from pathlib import Path

VERSION = 'bubble-studio-2.9.0'
# Refinement changes require a fresh analysis of unverified checkpoints.
ENGINE_VERSION = 'bubble-studio-2.9.0'
CHOICES = {'direction': {'ltr', 'rtl'}, 'layout': {'auto', 'rows', 'columns', 'single'},
           'quality': {'precise', 'fast'}}
BOOLS = {'skip', 'include_free_text'}


def series_settings(source: Path, root: Path, defaults=None):
    """Apply root-to-series JSON overrides, rejecting typos instead of ignoring them."""
    source, root = source.resolve(), root.resolve()
    parent = source if source.is_dir() else source.parent
    relative = parent.relative_to(root)
    parts={p.casefold() for p in (*root.parts,*relative.parts)}
    manga=any(p=='manga' or 'mangaplus' in p or 'shonenjump' in p for p in parts)
    result = {'direction': 'rtl' if manga else 'ltr',
              'layout': 'auto', 'quality': 'precise', 'skip': False, 'include_free_text': False}
    result.update(defaults or {})
    for folder in [root, *(root.joinpath(*relative.parts[:n]) for n in range(1, len(relative.parts)+1))]:
        config = folder / 'bubble-studio.json'
        if not config.is_file():
            continue
        if config.stat().st_size > 16384:
            raise ValueError(f'Zbyt duża konfiguracja: {config}')
        values = json.loads(config.read_text(encoding='utf-8-sig'))
        if not isinstance(values, dict) or set(values) - (set(CHOICES) | BOOLS):
            raise ValueError(f'Nieznane ustawienia w {config}')
        for key, value in values.items():
            if (key in BOOLS and type(value) is not bool) or (key in CHOICES and (not isinstance(value, str) or value not in CHOICES[key])):
                raise ValueError(f'Nieprawidłowe {key} w {config}')
        result.update(values)
    return result
