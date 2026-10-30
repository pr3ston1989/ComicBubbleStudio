"""Combine previously inspected development pages and unseen titles for a frozen run."""
import argparse
import json
import shutil
from pathlib import Path
from tools.bubble_studio.runner import atomic_json

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--development',type=Path,required=True)
    p.add_argument('--holdout',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Wybierz nowy folder')
    a.output.mkdir(parents=True)
    samples=[]
    seeds={}
    for source,split in [(a.development,'development'),(a.holdout,'holdout')]:
        manifest=json.loads((source/'sample.json').read_text(encoding='utf-8'))
        seeds[split]=manifest.get('seed')
        for sample in manifest['samples']:
            name=f'{len(samples):03}-'+sample['sha256'][:12]+'.png'
            shutil.copy2(source/sample['image'],a.output/name)
            samples.append({**sample,'image':name,'split':split})
    old={s['archive'] for s in samples if s['split']=='development'}
    assert not any(s['archive'] in old for s in samples if s['split']=='holdout')
    atomic_json(a.output/'sample.json',{'samples':samples,'seed':seeds,
        'note':'Development pages were inspected before iteration 3. Holdout pages come from previously unseen titles.'})
    print(len(samples))

if __name__=='__main__':main()
