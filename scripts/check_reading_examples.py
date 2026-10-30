"""Match visually annotated utterance anchors; do not infer mask accuracy."""
import argparse
import json
from pathlib import Path

def check(folder):
    reference=json.loads((Path(__file__).resolve().parents[1]/'tests'/'reading_examples.json').read_text(encoding='utf-8'))
    pages=[]
    for ref in reference['pages']:
        paths=list(folder.glob('*'+ref['sha_prefix']+'.json'))
        if len(paths)!=1:raise ValueError('Brak jednoznacznej strony: '+ref['name'])
        doc=json.loads(paths[0].read_text(encoding='utf-8'))
        matched=[]
        for x,y in ref['points']:
            boxes=[b for b in doc['result']['bubbles'] if b['x']<=x<=b['x']+b['w'] and b['y']<=y<=b['y']+b['h']]
            matched.append(min(boxes,key=lambda b:b['w']*b['h'])['order'] if boxes else None)
        ordered=[m for m in matched if m is not None]
        inversions=sum(a>b for i,a in enumerate(ordered) for b in ordered[i+1:])
        pages.append({'page':ref['name'],'expected_utterances':len(matched),'matched_orders':matched,
                      'missing_anchors':matched.count(None),'inversions':inversions,
                      'extra_stops':max(0,len(doc['result']['bubbles'])-len(set(ordered)))})
    return {'passed':not any(p['missing_anchors'] or p['inversions'] for p in pages),
            'pages':pages,'note':reference['note']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();value=check(a.results);a.output.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(value,ensure_ascii=False))
    return 0 if value['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
