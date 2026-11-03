"""Strict, inherited per-series settings without executable configuration."""

import json
from pathlib import Path

VERSION = 'bubble-studio-2.11.3'
# Refinement changes require a fresh analysis of unverified checkpoints.
ENGINE_VERSION = 'bubble-studio-2.11.1'
CHOICES = {'direction': {'ltr', 'rtl'}, 'layout': {'auto', 'rows', 'columns', 'single'},
           'quality': {'precise', 'fast'}, 'reading_mode': {'auto', 'four_panel_strips'}}
BOOLS = {'skip', 'include_free_text'}


def series_settings(source: Path, root: Path, defaults=None):
    """Apply root-to-series JSON overrides, rejecting typos instead of ignoring them."""
    source, root = source.resolve(), root.resolve()
    parent = source if source.is_dir() else source.parent
    relative = parent.relative_to(root)
    parts={p.casefold() for p in (*root.parts,*relative.parts)}
    manga=any(p=='manga' or 'mangaplus' in p or 'shonenjump' in p for p in parts)
    result = {'direction': 'rtl' if manga else 'ltr',
              'layout': 'auto', 'reading_mode': 'auto', 'quality': 'precise', 'skip': False, 'include_free_text': False}
    result.update(defaults or {})
    configs = [folder / 'bubble-studio.json' for folder in [root, *(root.joinpath(*relative.parts[:n]) for n in range(1, len(relative.parts)+1))]]
    if source.is_file():
        configs.append(reading_settings_path(source))
    for config in configs:
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


def reading_settings_path(source):
    source = Path(source)
    return source / 'bubble-studio.json' if source.is_dir() else source.with_name(source.name + '.bubble-studio.json')


def save_reading_mode(source, mode, direction=None):
    """Store a title override atomically without changing neighbouring titles."""
    if mode not in CHOICES['reading_mode'] or direction not in {None, 'ltr', 'rtl'}:
        raise ValueError('Nieprawidłowy układ lub kierunek czytania')
    source = Path(source)
    if not source.exists():
        raise ValueError('Wybierz istniejący komiks lub folder stron')
    path = reading_settings_path(source)
    if path.is_symlink():
        raise ValueError('Plik ustawień nie może być dowiązaniem')
    values = {}
    if path.exists():
        if path.stat().st_size > 16384:
            raise ValueError('Zbyt duży plik ustawień')
        values = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(values, dict) or set(values) - (set(CHOICES) | BOOLS):
            raise ValueError('Nieznane ustawienia w pliku tytułu')
        for key, value in values.items():
            if ((key in BOOLS and type(value) is not bool) or
                (key in CHOICES and (not isinstance(value, str) or value not in CHOICES[key]))):
                raise ValueError('Nieprawidłowe ustawienia tytułu')
    values['reading_mode'] = mode
    if mode == 'four_panel_strips':
        values['layout'] = 'auto'
    if direction is not None:
        values['direction'] = direction
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding='utf8')
    temporary.replace(path)
    return path
