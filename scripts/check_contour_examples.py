"""Test manually annotated original-image points, independently of model scores."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np


def check(folder):
    refs=json.loads((Path(__file__).resolve().parents[1]/'tests/contour_examples.json').read_text(encoding='utf-8'))
    results=[]
    for ref in refs['pages']:
        paths=list(folder.glob('*'+ref['sha_prefix']+'.json'))
        if len(paths)!=1:raise ValueError('Missing page: '+ref['sha_prefix'])
        doc=json.loads(paths[0].read_text(encoding='utf-8'))['result']
        b=next(b for b in doc['bubbles'] if b['id']==ref['region_id'])
        contours=[np.array([[(b['x']+p['x']*b['w'])*doc['width'],(b['y']+p['y']*b['h'])*doc['height']]
                            for p in poly],np.float32) for poly in b.get('polygons',[])]
        def inside(point):return any(cv2.pointPolygonTest(c,tuple(map(float,point)),False)>=0 for c in contours)
        failed=[{'point':p,'expected':'inside'} for p in ref['inside'] if not inside(p)]
        failed += [{'point':p,'expected':'outside'} for p in ref['outside'] if inside(p)]
        results.append({'page':ref['name'],'region_id':ref['region_id'],'points':len(ref['inside'])+len(ref['outside']),'errors':failed})
    return {'passed':not any(r['errors'] for r in results),'pages':results,'note':refs['note']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=check(a.results)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
