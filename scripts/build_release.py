"""Auditable bootstrap distribution: no user comics, caches or private runtime."""
from pathlib import Path
import hashlib
import json
import zipfile
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.bubble_studio.config import VERSION as PIPELINE_VERSION
VERSION=PIPELINE_VERSION.removeprefix('bubble-studio-')
TOP=['START.bat','START.vbs','START_KONSOLA.bat','SPRAWDZ.bat','PRZETWORZ.bat','DIAGNOSTYKA.bat',
     'INSTALUJ.bat','INSTALUJ.ps1','README.md','RESEARCH.md','JAKOSC.md']

def build():
    files=[ROOT/name for name in TOP]
    files+=[p for p in (ROOT/'tools'/'bubble_studio').iterdir()
            if p.is_file() and p.suffix in {'.py','.ps1','.bat','.html','.md','.txt'} and '.before-' not in p.name]
    files+=[ROOT/'web'/'backend'/name for name in
            ['__init__.py','comic_archive.py','comic_bubble_package.py','comic_smartview_layout.py']]
    files+=list((ROOT/'assets').glob('*'))
    files+=[p for p in (ROOT/'docs').iterdir() if p.suffix=='.md']
    files+=[p for p in (ROOT/'scripts').iterdir() if p.suffix in {'.py','.ps1','.cs','.cjs'}]
    files+=list((ROOT/'tests').glob('test_*.py'))
    files+=list((ROOT/'tests').glob('*.json'))
    files+=list((ROOT/'tests'/'fixtures').glob('*.pdf'))
    files=sorted(set(files))
    # Windows PowerShell 5.1 requires a BOM to recognise UTF-8 source text.
    for p in files:
        if p.suffix=='.ps1':
            source=p.read_text(encoding='utf-8-sig')
            p.write_text(source,encoding='utf-8-sig')
    manifest={'format':'nokturn-bubble-studio-release-v1','version':VERSION,
              'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (ROOT/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    out=ROOT/'dist'/f'Nokturn-Bubble-Studio-{VERSION}-windows-x64.zip'
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[ROOT/'release-manifest.json']:
            z.write(p,'Nokturn-Bubble-Studio/'+p.relative_to(ROOT).as_posix())
        for folder in ('WEJSCIE/Komiksy','WEJSCIE/Manga','WEJSCIE/Manhua','GOTOWE','PRACA'):
            z.writestr('Nokturn-Bubble-Studio/'+folder+'/',b'')
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for entry in manifest['files']:
            assert hashlib.sha256(z.read('Nokturn-Bubble-Studio/'+entry['path'])).hexdigest()==entry['sha256']
    out.with_suffix('.zip.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n',encoding='ascii')
    print(out)
    return out

if __name__=='__main__': build()
