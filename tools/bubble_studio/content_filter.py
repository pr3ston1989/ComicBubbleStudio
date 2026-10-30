"""Reversible removal of narrowly confirmed non-story text, with spatial evidence."""
from __future__ import annotations
import copy
import math
import re
from .geometry import area,intersection
from .textcheck import pixel_box


def compact(text):
    return re.sub(r'[^a-z0-9]','',''.join(text).casefold())


def valid_rows(rows,size):
    w,h=size
    return [r for r in rows if r.get('score',0)>=.9 and len(r.get('box',[]))==4
            and all(math.isfinite(v) for v in r['box'])
            and 0<=r['box'][0]<r['box'][2]<=w and 0<=r['box'][1]<r['box'][3]<=h]


def event_ad_evidence(document,rows):
    """Require a frameless event announcement, a release schedule and a CTA.

    A repeated title, URL, isolated marketing phrase or footer is insufficient.
    Any detected story panel prevents automatic whole-page removal.
    """
    result=document['result'];w,h=result['width'],result['height']
    if result['panels']:return None
    headers=[r for r in rows if r['box'][1]<.5*h and 'crossoverevent' in compact(r['text'])]
    dates={m for r in rows for m in re.findall(r'\b\d{2}/\d{2}/\d{2,4}\b',r['text'])}
    weeks=[r for r in rows if re.fullmatch(r'week[1-9s]?',compact(r['text']))]
    if not headers or len(dates)<4 or len(weeks)<3:return None
    for a in rows:
        if compact(a['text'])!='readnow' or a['box'][1]<.5*h:continue
        for b in rows:
            if compact(b['text'])!='forfree':continue
            height=max(a['box'][3]-a['box'][1],b['box'][3]-b['box'][1])
            x_overlap=max(0,min(a['box'][2],b['box'][2])-max(a['box'][0],b['box'][0]))
            if (0<=b['box'][1]-a['box'][3]<=1.5*height
                    and x_overlap>=.7*min(a['box'][2]-a['box'][0],b['box'][2]-b['box'][0])
                    and a['box'][1]-min(r['box'][1] for r in headers)>=.5*h):
                return {'kind':'scheduled-event-ad','header':headers,'cta':[a,b],
                        'distinct_dates':sorted(dates),'week_labels':weeks,
                        'note':'No detected panels; independent event announcement, multi-date schedule and spatially paired READ NOW / FOR FREE.'}
    return None


def credit_label(text):
    match=re.fullmatch(r'\s*(translation|lettering)\s*:\s*(.+?)\s*',text,re.I)
    if not match:return None
    name=match[2]
    if (sum(c.isalpha() for c in name)<5 or any(not(c.isalpha() or c in " '-’.") for c in name)
            or len(name.split())>6):return None
    return match[1].lower()


def credit_regions(document,rows):
    result=document['result'];size=(result['width'],result['height']);w,h=size
    labels=[r for r in rows if credit_label(r['text']) and (r['box'][3]-r['box'][1])<.025*h
            and max((intersection(r['box'],pixel_box(p,size))/max(1,area(r['box'])) for p in result['panels']),default=0)<.5]
    paired=[]
    for a in labels:
        for b in labels:
            if credit_label(a['text'])==credit_label(b['text']):continue
            ah=a['box'][3]-a['box'][1];bh=b['box'][3]-b['box'][1]
            overlap=min(a['box'][3],b['box'][3])-max(a['box'][1],b['box'][1])
            gap=max(a['box'][0],b['box'][0])-min(a['box'][2],b['box'][2])
            if .7<=ah/bh<=1.4 and overlap>=.8*min(ah,bh) and gap>=min(ah,bh):
                paired.append(a);break
    checks={r['region_id']:r for r in document.get('analysis',{}).get('text_check',{}).get('regions',[])}
    removed=[];evidence=[]
    for bubble in result['bubbles']:
        if bubble.get('type')!='text' or bubble.get('polygons') or bubble.get('polygon'):continue
        check=checks.get(bubble['id']);ocr=check.get('ocr',[]) if check else []
        if len(ocr)!=1 or ocr[0].get('score',0)<.9 or not credit_label(ocr[0]['text']):continue
        box=pixel_box(bubble,size)
        for row in paired:
            if (compact(row['text'])==compact(ocr[0]['text'])
                    and intersection(box,row['box'])/max(1,area(row['box']))>.995
                    and area(box)<=3*area(row['box'])):
                removed.append(bubble['id']);evidence.append({'region_id':bubble['id'],'row':row});break
    return removed,evidence


def collage_evidence(rows,size):
    """Repetition is only a review signal; it never authorizes deleting speech."""
    w,h=size;groups={}
    for r in rows:
        word=compact(r['text'])
        if 5<=len(word)<=24 and len(set(word))>=3 and r['box'][3]-r['box'][1]<.025*h:
            groups.setdefault(word,[]).append(r)
    for word,group in groups.items():
        cells={(int(r['box'][0]/w*8),int(r['box'][1]/h*8)) for r in group}
        if len(group)>=12 and len(cells)>=12:
            return {'kind':'possible-cover-collage','repeated_text':word,'occurrences':len(group),'grid_cells':len(cells),
                    'note':'Repetition alone cannot distinguish promotional covers from genuine repeated dialogue. Review only.'}
    return None


def apply_content_filter(document,all_lines):
    result=document['result'];size=(result['width'],result['height']);rows=valid_rows(all_lines,size)
    advertisement=event_ad_evidence(document,rows)
    removed,evidence=credit_regions(document,rows) if not advertisement else ([],[])
    if advertisement:removed=[b['id'] for b in result['bubbles']]
    collage=collage_evidence(rows,size)
    if not removed:
        if collage:
            document['analysis']['content_filter']={'status':'review-only','evidence':collage,'removed_region_ids':[]}
            document['review']['flags'].append('Możliwa mozaika okładek: powtarzające się tytuły. Zachowano wszystkie regiony; sprawdź, czy strona jest reklamą')
        return document
    original={'result':copy.deepcopy(result),'reading_anchors':copy.deepcopy(document['analysis'].get('reading_anchors',{})),
              'text_check':copy.deepcopy(document['analysis'].get('text_check')),'review':copy.deepcopy(document['review'])}
    kept=[b for b in result['bubbles'] if b['id'] not in removed];mapping={b['id']:f'b{i+1}' for i,b in enumerate(kept)}
    for i,b in enumerate(kept):b['id']=f'b{i+1}';b['order']=i+1
    result['bubbles']=kept;result['confidence']=sum(b['confidence'] for b in kept)/max(1,len(kept))
    document['analysis']['reading_anchors']={mapping[k]:v for k,v in original['reading_anchors'].items() if k in mapping}
    check=document['analysis'].get('text_check')
    if check:check['regions']=[dict(r,region_id=mapping[r['region_id']]) for r in check['regions'] if r['region_id'] in mapping]
    def active_flag(flag):
        ids=re.findall(r'\bb\d+\b',flag)
        if any(i in removed for i in ids):return None
        return re.sub(r'\bb\d+\b',lambda m:mapping.get(m[0],m[0]),flag)
    flags=[] if advertisement else [x for f in document['review']['flags'] if (x:=active_flag(f))]
    flags.append('Pominięto stronę reklamową z harmonogramem wydań; oryginalne regiony zachowano do przywrócenia' if advertisement
                 else 'Pominięto sparowane kredyty tłumaczenia i liternictwa poza kadrami; oryginalne regiony zachowano do przywrócenia')
    document['review']['flags']=list(dict.fromkeys(flags));document['review']['verified']=False
    document['analysis']['content_filter']={'status':'applied','kind':'event-ad' if advertisement else 'editorial-credits',
       'removed_region_ids':removed,'preserved_id_mapping':mapping,'evidence':advertisement or evidence,'original':original}
    return document


def restore_content_filter(document):
    """Restore the complete pre-filter reading result, without invoking a model."""
    audit=document.get('analysis',{}).get('content_filter',{})
    if audit.get('status')!='applied' or not audit.get('original'):return False
    original=copy.deepcopy(audit['original']);document['result']=original['result']
    document['analysis']['reading_anchors']=original['reading_anchors']
    if original['text_check'] is not None:document['analysis']['text_check']=original['text_check']
    document['review']=original['review'];document['review']['verified']=False
    audit['status']='restored';return True
