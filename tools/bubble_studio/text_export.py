"""Optional CPU-only text export; never writes the comic or its Nokturn package."""
from __future__ import annotations
import argparse
import html
import io
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from web.backend.comic_archive import read_entry
from web.backend.comic_bubble_package import load_package
from web.backend.comic_smartview_layout import order_boxes_by_cuts
from .textcheck import pixel_box
from .quality_guard import _polygons

FORMATS={'html','txt','md'}


def _mask(bubble,size,origin=(0,0),shape=None):
    width,height=size
    result=np.zeros(shape or (height,width),np.uint8)
    if bubble.get('polygons'):cv2.fillPoly(result,_polygons(bubble,width,height,origin),1)
    else:
        a,b,c,d=pixel_box(bubble,size);a,c=max(0,a-origin[0]),min(result.shape[1],c-origin[0]);b,d=max(0,b-origin[1]),min(result.shape[0],d-origin[1]);result[b:d,a:c]=1
    return result


def _covered(mask,box):
    a,b,c,d=map(float,box)
    dx,dy=int((c-a)*.1),int((d-b)*.1)
    a,b,c,d=int(a+dx),int(b+dy),int(np.ceil(c-dx)),int(np.ceil(d-dy))
    area=max(0,c-a)*max(0,d-b)
    if not area:return 0
    a,c=max(0,a),min(mask.shape[1],c);b,d=max(0,b),min(mask.shape[0],d)
    return float(np.sum(mask[b:d,a:c]))/area if c>a and d>b else 0


def _overlap(a,b):
    hit=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return hit/max(1,min((a[2]-a[0])*(a[3]-a[1]),(b[2]-b[0])*(b[3]-b[1])))


def _merge_native(ocr,native):
    # Prefer the actual PDF string where the image and text layer refer to the
    # same line, while retaining OCR-only parts of a mixed page.
    output=[]
    compact=lambda s:''.join(c.casefold() for c in unicodedata.normalize('NFKD',s.replace('ł','l').replace('Ł','L')) if c.isalnum())
    for row in ocr:
        matches=[n for n in native if _overlap(row['box'],n['box'])>.5]
        actual=compact(' '.join(n['text'] for n in sorted(matches,key=lambda n:(n['box'][1],n['box'][0]))));recognized=compact(row['text'])
        agreement=bool(actual and recognized and .85<=len(actual)/len(recognized)<=1.2 and SequenceMatcher(None,actual,recognized).ratio()>=.75)
        # OCR may split a complete native PDF line into word fragments. Match
        # each fragment only when it lies on that line and is supported by its
        # string; a wider mixed native/scan row must keep its OCR-only suffix.
        fragment=False
        for candidate in matches:
            x,y,xx,yy=candidate['box'];a,b,c,d=row['box']
            horizontal=max(0,min(c,xx)-max(a,x))/max(1,c-a)
            aligned=y-(yy-y)*.2<=(b+d)/2<=yy+(yy-y)*.2
            value=compact(candidate['text'])
            common=SequenceMatcher(None,recognized,value).find_longest_match().size
            if horizontal>=.9 and aligned and len(recognized)>=3 and common>=len(recognized)*.85:
                fragment=True;break
        a,b,c,d=row['box'];width,height=max(1,int(np.ceil(c-a))),max(1,int(np.ceil(d-b)));coverage=0
        if matches and width*height<=4_000_000:
            covered=np.zeros((height,width),np.uint8)
            for candidate in matches:
                x,y,xx,yy=candidate['box'];x,xx=max(0,int(x-a-3)),min(width,int(np.ceil(xx-a+3)));y,yy=max(0,int(y-b-3)),min(height,int(np.ceil(yy-b+3)))
                if xx>x and yy>y:covered[y:yy,x:xx]=1
            coverage=float(np.mean(covered))
        if agreement or fragment or coverage>=.9:continue
        if matches:row=dict(row,merge_uncertain=True)
        output.append(row)
    for row in native:
        if not any(r['text']==row['text'] and _overlap(r['box'],row['box'])>.8 for r in output):output.append(row)
    return output


def _ordered_lines(rows,mask,origin,direction):
    if not rows:return []
    # Remove thin physical connectors in a copy, to read complete lobes before
    # moving to the next lobe instead of interleaving their individual lines.
    size=max(5,round(min(mask.shape)*.10))|1
    opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size)))
    _,labels,stats,_=cv2.connectedComponentsWithStats(opened,8);groups={}
    for row in rows:
        a,b,c,d=row['box'];cx,cy=round((a+c)/2-origin[0]),round((b+d)/2-origin[1]);label=int(labels[cy,cx]) if 0<=cy<labels.shape[0] and 0<=cx<labels.shape[1] else 0
        if label and stats[label,-1]<np.sum(mask)*.04:label=0
        groups.setdefault(label,[]).append(row)
    def line_sequence(items):
        # Broad joins can survive opening. Separate full text columns only
        # when the actual balloon narrows in the empty gap between them;
        # ordinary word gaps inside one oval must remain line-by-line.
        columns=[]
        for row in sorted(items,key=lambda r:r['box'][0]):
            if not columns or row['box'][0]>max(r['box'][2] for r in columns[-1]):columns.append([])
            columns[-1].append(row)
        projection=mask.sum(axis=0)
        for split in range(1,len(columns)):
            left=[r for col in columns[:split] for r in col];right=[r for col in columns[split:] for r in col]
            if min(len(left),len(right))<2:continue
            bounds=lambda group:[min(r['box'][0] for r in group),min(r['box'][1] for r in group),max(r['box'][2] for r in group),max(r['box'][3] for r in group)]
            a,b=bounds(left),bounds(right)
            if min(a[3],b[3])-max(a[1],b[1])<.5*min(a[3]-a[1],b[3]-b[1]):continue
            start,end=int(np.ceil(a[2]-origin[0])),int(b[0]-origin[0])
            centers=[round((v[0]+v[2])/2-origin[0]) for v in (a,b)]
            if not 0<=start<end<=mask.shape[1] or not all(0<=c<mask.shape[1] for c in centers):continue
            body=min(projection[c] for c in centers)
            if body and np.min(projection[start:end])<=body*.72:
                sequence=[left,right] if direction=='ltr' else [right,left]
                return [r for group in sequence for r in line_sequence(group)]
        bands=[]
        for row in sorted(items,key=lambda r:((r['box'][1]+r['box'][3])/2,r['box'][0])):
            a,b,c,d=row['box'];matches=[]
            for i,band in enumerate(bands):
                top=min(r['box'][1] for r in band);bottom=max(r['box'][3] for r in band)
                if min(d,bottom)-max(b,top)>=.5*min(d-b,bottom-top):matches.append(i)
            if matches:bands[matches[0]].append(row)
            else:bands.append([row])
        return [r for band in sorted(bands,key=lambda band:min(r['box'][1] for r in band)) for r in sorted(band,key=lambda r:r['box'][0])]
    if 0 in groups or len(groups)<2:return line_sequence(rows)
    proxies=[]
    for label,group in groups.items():
        x,y,w,h,_=stats[label];proxies.append(dict(x=float(x)/mask.shape[1],y=float(y)/mask.shape[0],w=float(w)/mask.shape[1],h=float(h)/mask.shape[0],group=group))
    ordered=order_boxes_by_cuts(proxies,direction,page_aspect=mask.shape[0]/max(1,mask.shape[1]),layout='auto')
    return [r for proxy in ordered for r in line_sequence(proxy['group'])]


def extract_page(image,document,checker,native_rows=None,all_text=False):
    result=document['result'];regions=[];occupied=np.zeros((image.height,image.width),np.uint8)
    for bubble in sorted(result['bubbles'],key=lambda b:b['order']):
        roi=pixel_box(bubble,image.size);crop=image.crop(roi);mask=_mask(bubble,image.size,roi[:2],(crop.height,crop.width))
        rgb=np.asarray(crop).copy();pixels=rgb[mask>0];paper=np.median(pixels,axis=0).astype(np.uint8) if len(pixels) else np.array([255,255,255],np.uint8);rgb[mask==0]=paper
        rows=[]
        for row in checker.read(Image.fromarray(rgb)):
            a,b,c,d=row['box'];box=[a*crop.width,b*crop.height,c*crop.width,d*crop.height]
            if not row.get('text','').strip() or _covered(mask,box)<.85:continue
            rows.append(dict(text=row['text'].strip(),score=float(row['score']),box=[box[0]+roi[0],box[1]+roi[1],box[2]+roi[0],box[3]+roi[1]],source='ocr'))
        native=[]
        for row in native_rows or []:
            local=[v-o for v,o in zip(row['box'],(*roi[:2],*roi[:2]))]
            if _covered(mask,local)>=.85:native.append(dict(row))
        rows=_merge_native(rows,native);rows=_ordered_lines(rows,mask,roi[:2],result['direction'])
        occupied[roi[1]:roi[3],roi[0]:roi[2]]|=mask
        text='\n'.join(r['text'] for r in rows)
        regions.append(dict(id=bubble['id'],order=bubble['order'],text=text,lines=rows,
                            uncertain=not text or any(r.get('merge_uncertain') or r['source']=='ocr' and r['score']<.85 for r in rows)))
    extra=[]
    if all_text:
        raw=[dict(r,source='ocr') for r in checker.locate_context(image)]
        raw=_merge_native(raw,native_rows or [])
        for row in raw:
            if _covered(occupied,row['box'])<.5:extra.append(row)
        proxies=[dict(x=r['box'][0]/image.width,y=r['box'][1]/image.height,w=(r['box'][2]-r['box'][0])/image.width,h=(r['box'][3]-r['box'][1])/image.height,row=r) for r in extra]
        extra=[r['row'] for r in order_boxes_by_cuts(proxies,result['direction'],page_aspect=image.height/image.width,layout='auto')]
    return dict(direction=result['direction'],regions=regions,extra=extra)


def write_exports(base,title,pages,format='html'):
    if format not in FORMATS:raise ValueError('Nieznany format eksportu tekstu')
    base=Path(base);base.parent.mkdir(parents=True,exist_ok=True);parts=[title,'Tekst do sprawdzenia i tłumaczenia. OCR może zawierać błędy.',''];sections=[]
    for page in pages:
        heading=f"Strona {page['page']} — {page['filename']}";parts.extend([heading,'='*len(heading),'']);body=[]
        for row in page['regions']:
            text=row['text'] or '[Brak odczytu — sprawdź obraz]';warning=' · do sprawdzenia' if row['uncertain'] else ''
            parts.extend([f"{row['order']}. {text}{warning}",''])
            body.append(f'<article><h3>{row["order"]}{html.escape(warning)}</h3><p dir="auto">{html.escape(text).replace(chr(10),"<br>")}</p></article>')
        if page['extra']:
            parts.extend(['Pozostałe napisy poza listą dymków — do sprawdzenia',''])
            body.append('<h3>Pozostałe napisy poza listą dymków</h3>')
            for row in page['extra']:parts.extend([row['text'],'']);body.append(f'<p dir="auto">{html.escape(row["text"])}</p>')
        if not page['regions'] and not page['extra']:parts.extend(['[Brak tekstu w wybranym zakresie]','']);body.append('<p>Brak tekstu w wybranym zakresie.</p>')
        if page.get('native_error'):parts.extend(['[Warstwa tekstowa PDF niedostępna; użyto OCR]',''])
        sections.append(f'<section><h2>{html.escape(heading)}</h2>'+''.join(body)+'</section>')
    suffixes=['txt','html'] if format=='html' else [format];files=[]
    for suffix in suffixes:
        path=Path(str(base)+'.tekst.'+suffix)
        if suffix=='html':
            content='<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{max-width:850px;margin:30px auto;padding:0 22px;color:#202020;background:white;font:18px/1.6 system-ui}h1,h2,h3{line-height:1.3}section{margin-top:36px}article{margin:20px 0}article h3{font-size:15px;color:#555;margin-bottom:4px}p{margin-top:4px}h2{font-size:23px;overflow-wrap:anywhere}@media print{section{break-before:page}article{break-inside:avoid}body{font:12pt/1.5 Arial}}</style><h1>'+html.escape(title)+'</h1><p>Tekst do sprawdzenia i tłumaczenia. Numery odpowiadają kolejności w pakiecie Nokturna. OCR może zawierać błędy.</p>'+''.join(sections)+'</html>'
        else:content='\n'.join(parts)
        temporary=path.with_name(path.name+'.partial');temporary.write_text(content,encoding='utf-8-sig' if suffix=='txt' else 'utf8');temporary.replace(path);files.append(str(path))
    audit=Path(str(base)+'.tekst.json');tmp=audit.with_name(audit.name+'.partial');tmp.write_text(json.dumps(dict(schema=1,title=title,pages=pages,note='Optional export only; comic and bubble package are not changed.'),ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(audit);files.append(str(audit))
    return files


def export_comic(source,format='html',all_text=False,checker=None,native_layers=None,progress=None):
    source=Path(source);package=load_package(source)
    if package is None:raise ValueError('Brak zgodnego, gotowego pakietu dymków. Najpierw przygotuj komiks w Bubble Studio.')
    if checker is None:
        from .textcheck import TextCheck
        checker=TextCheck()
    pages=[]
    for index,record in enumerate(package.manifest['pages']):
        document=package.page(index);data=read_entry(source,record['name'])
        with Image.open(io.BytesIO(data)) as raw:image=ImageOps.exif_transpose(raw).convert('RGB')
        layer=native_layers[index] if native_layers else dict(rows=[],error=None)
        page=extract_page(image,document,checker,layer['rows'],all_text)
        page.update(page=index+1,filename=record['name'],native_error=layer.get('error'));pages.append(page)
        if progress:progress(index+1,len(package.manifest['pages']))
    base=source/source.name if source.is_dir() else source
    return write_exports(base,source.stem,pages,format)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Dodatkowy eksport tekstu z gotowego komiksu bez zmiany dymków')
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--format',choices=sorted(FORMATS),default='html');parser.add_argument('--all-text',action='store_true')
    args=parser.parse_args(argv);files=export_comic(args.source,args.format,args.all_text)
    print('\n'.join(files),flush=True)


if __name__=='__main__':main()
