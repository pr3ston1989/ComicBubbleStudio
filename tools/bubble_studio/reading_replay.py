"""Replay layout from exact saved text anchors, without rerunning segmentation."""
import argparse,copy,hashlib,json,re,math
from pathlib import Path
from PIL import Image
from .geometry import ordered_result


def layout_signature():
    sources=[Path(__file__).with_name('geometry.py'),Path(__file__).resolve().parents[2]/'web/backend/comic_smartview_layout.py']
    return hashlib.sha256(b''.join(p.name.encode()+p.read_bytes() for p in sources)).hexdigest()


def reorder(document,orderer=None):
    doc=copy.deepcopy(document);before=doc['result'];anchors=doc.get('analysis',{}).get('reading_anchors')
    if not anchors or set(anchors)!={b['id'] for b in before['bubbles']}:
        if before['bubbles']:raise ValueError('Missing exact inference reading anchors')
        anchors={}
    if before.get('crop')!={'x':0,'y':0,'w':1,'h':1}:
        raise ValueError('Replay requires an unedited full-page inference result')
    bubbles=before['bubbles'];identities={id(b):b['id'] for b in bubbles}
    for b in bubbles:
        anchor=anchors[b['id']]
        if set(anchor)!={'x','y','w','h'}:raise ValueError('Invalid saved reading anchor')
        if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in anchor.values())
                or anchor['w']<=0 or anchor['h']<=0 or anchor['x']+anchor['w']>1.000001 or anchor['y']+anchor['h']>1.000001):
            raise ValueError('Invalid saved reading anchor coordinates')
        b['_reading_box']=dict(anchor)
    result=(orderer or ordered_result)(before['panels'],bubbles,before['width'],before['height'],before['direction'],before['layout'])
    mapping={identities[id(b)]:b['id'] for b in result['bubbles']}
    doc['result']=result
    doc['analysis']['reading_anchors']={mapping[old]:anchor for old,anchor in anchors.items()}
    for row in doc.get('analysis',{}).get('text_check',{}).get('regions',[]):row['region_id']=mapping[row['region_id']]
    doc['review']['flags']=[re.sub(r'\bb\d+\b',lambda m:mapping.get(m[0],m[0]),s) for s in doc['review']['flags']]
    # Retain the original GPU signature. A separate record identifies the
    # replayed layout code; never relabel cached inference as fresh GPU output.
    doc['layout_replay']={'kind':'layout-only','inference_code_sha256':document['lab']['code_sha256'],
                          'layout_code_sha256':layout_signature()}
    return doc


def main(argv=None):
    p=argparse.ArgumentParser(description='Ponowne liczenie kolejności z zapisanych kotwic tekstu')
    p.add_argument('--input',type=Path,required=True);p.add_argument('--images',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--verify-identity',action='store_true')
    a=p.parse_args(argv)
    if not a.verify_identity and (not a.images or not a.output):p.error('Wymagane --images i --output')
    if a.output and a.output.exists():p.error('Wybierz nowy folder wyników')
    files=sorted(f for f in a.input.glob('*.json') if f.name!='results.json');count=0
    if not files:p.error('Brak wyników')
    if a.output:a.output.mkdir(parents=True)
    for file in files:
        doc=json.loads(file.read_text(encoding='utf-8'));new=reorder(doc)
        if a.verify_identity:
            if new['result']!=doc['result']:raise ValueError('Layout replay differs: '+file.name)
        else:
            image=a.images/(file.stem+'.png')
            if hashlib.sha256(image.read_bytes()).hexdigest()!=doc['lab']['sha256']:raise ValueError('Image identity differs')
            (a.output/file.name).write_text(json.dumps(new,ensure_ascii=False),encoding='utf-8')
            from .quality_lab import overlay
            with Image.open(image) as raw:overlay(raw.convert('RGB'),new,a.output/(file.stem+'-overlay.png'))
        count+=1
    if a.output:
        from .quality_lab import report
        records=json.loads((a.input/'results.json').read_text(encoding='utf-8'))
        records['layout_replay']={'layout_code_sha256':layout_signature(),'input':str(a.input),
                                 'note':'GPU inference times are retained from source. Only layout was replayed.'}
        for record in records['pages']:
            d=json.loads((a.output/record['data']).read_text(encoding='utf-8'));record['flags']=d['review']['flags']
        (a.output/'results.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
        report(a.images,a.output,records['pages'])
    print(json.dumps({'pages':count,'identity_verified':a.verify_identity,'layout_code_sha256':layout_signature()}))
    return 0


if __name__=='__main__':raise SystemExit(main())
