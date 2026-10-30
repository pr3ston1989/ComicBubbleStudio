"""Local page understanding constrained by OCR, geometry and reversible edits."""
from __future__ import annotations
import copy
import hashlib
import json
import re
import time
import os
from pathlib import Path
import numpy as np
from .context_prompts import PAGE_PROMPT,STRUCTURED_PROMPT,ROLE_PROMPT
from .context_layout import layout,prose_groups,field
from .geometry import rectangle,padded_box,ordered_result,intersection,area
from .textcheck import pixel_box

MODEL_MANIFEST=Path(__file__).resolve().parents[2]/'assets/context-model.json'


def model_manifest():
    return json.loads(MODEL_MANIFEST.read_text(encoding='utf8'))


def default_weights():
    return Path(__file__).with_name('.runtime')/'models/page-context-qwen3-vl-4b'


def prepare_context_model(folder=None):
    """Download only pinned data files, never executable model repository code."""
    folder=Path(folder or default_weights());manifest=model_manifest()
    missing=[r for r in manifest['files'] if not (folder/r['path']).is_file()]
    if missing:
        from huggingface_hub import snapshot_download,constants
        constants.HF_HUB_DOWNLOAD_TIMEOUT=max(60,constants.HF_HUB_DOWNLOAD_TIMEOUT)
        print('Pobieranie lokalnego modelu rozumienia stron (około 9 GB)…',flush=True)
        snapshot_download(manifest['repository'],revision=manifest['revision'],local_dir=folder,
                          allow_patterns=[r['path'] for r in manifest['files']],max_workers=2)
    for r in manifest['files']:
        if Path(r['path']).name!=r['path']:raise RuntimeError('Nieprawidłowa nazwa pliku modelu')
        with (folder/r['path']).open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=r['sha256']:
            raise RuntimeError('Nieprawidłowa suma kontrolna modelu rozumienia stron')
    return folder


def parse_answer(text):
    if not isinstance(text,str):return None
    try:
        value=json.loads(text.strip().removeprefix('```json').removeprefix('```').removesuffix('```'))
        return value if isinstance(value,dict) else None
    except (ValueError,TypeError):return None


def valid_classification(value):
    return (isinstance(value,dict) and value.get('kind') in {'story','character_profile','story_recap',
        'cover_gallery','advertisement','credits','illustration','mixed'}
        and type(value.get('contains_readable_story')) is bool)


def region_candidate(bubble,anchor,ocr):
    # A narrow real balloon or rectangular caption can look like an isolated
    # sound/sign after cropping. A crop classifier cannot discard an existing
    # contour; retain that independent geometric evidence for human review.
    if bubble.get('polygons') or bubble.get('polygon'):return False
    text=' '.join(r.get('text','') for r in ocr if r.get('score',0)>=.75)
    return (sum(c.isalpha() for c in text)>=3 and
            (bubble.get('type')=='text' or (bubble['w']*bubble['h']<.05
             and bubble['w']*bubble['h']<2*anchor['w']*anchor['h'])))


def omission_allowed(classification,ocr):
    if not isinstance(classification,dict) or classification.get('enclosure')!='none':return False
    role=classification.get('role')
    text=' '.join(r.get('text','') for r in ocr if r.get('score',0)>=.75)
    if sum(c.isalpha() for c in text)<3:return False
    if role in {'physical_sign','mechanical_sound'}:return True
    if role=='editorial':
        compact=re.sub('[^a-z]','',text.lower())
        markers=('writer','artist','letterer','lettering','colorist','colors','editor','variantcover','copyright','allrightsreserved')
        return sum(compact.count(word) for word in markers)>=2
    return False


def renumber_after_omission(document,removed):
    result=document['result'];analysis=document['analysis'];old=copy.deepcopy(analysis.get('reading_anchors',{}))
    kept=[b for b in result['bubbles'] if b['id'] not in removed];mapping={b['id']:f'b{i+1}' for i,b in enumerate(kept)}
    for i,b in enumerate(kept):b.update(id=f'b{i+1}',order=i+1)
    result['bubbles']=kept;result['confidence']=sum(b['confidence'] for b in kept)/max(1,len(kept))
    analysis['reading_anchors']={mapping[k]:v for k,v in old.items() if k in mapping}
    check=analysis.get('text_check')
    if check:check['regions']=[dict(r,region_id=mapping[r['region_id']]) for r in check['regions'] if r['region_id'] in mapping]
    flags=[]
    for flag in document['review']['flags']:
        if any(i in removed for i in re.findall(r'\bb\d+\b',flag)):continue
        flags.append(re.sub(r'\bb\d+\b',lambda m:mapping.get(m[0],m[0]),flag))
    document['review']['flags']=flags
    return mapping


class SemanticPage:
    """Pinned Qwen model; its proposals never become correctness percentages."""
    def __init__(self,weights_dir=None,cache_dir=None,strict=False):
        self.weights_dir=Path(weights_dir or os.environ.get('NOKTURN_CONTEXT_MODEL') or default_weights())
        self.cache_dir=Path(cache_dir or os.environ.get('NOKTURN_CONTEXT_CACHE') or self.weights_dir.parent/'context-cache')
        self.strict=strict;self.model=None;self.processor=None;self.calls=[]
        manifest=model_manifest()
        self.provenance={k:manifest[k] for k in ('repository','revision','license')}
        self.provenance['files']=manifest['files']

    def _load(self):
        if self.model is not None:
            self.model.to('cuda')
            return
        import torch
        from transformers import Qwen3VLForConditionalGeneration,AutoProcessor
        torch.set_num_threads(6)
        folder=prepare_context_model(self.weights_dir)
        print('Wczytywanie lokalnego modelu rozumienia stron…',flush=True)
        torch.cuda.empty_cache()
        self.model=Qwen3VLForConditionalGeneration.from_pretrained(folder,dtype=torch.bfloat16,
            attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).to('cuda').eval()
        self.processor=AutoProcessor.from_pretrained(folder,local_files_only=True,trust_remote_code=False)

    def park(self):
        """Leave VRAM available for full-resolution segmentation of the next page."""
        if self.model is not None:
            import torch
            self.model.to('cpu')
            torch.cuda.empty_cache()

    def _ask(self,images,prompt,max_tokens=100):
        signature=hashlib.sha256((self.provenance['revision']+str(max_tokens)+prompt).encode())
        for im in images:signature.update(str(im.size).encode());signature.update(np.asarray(im).tobytes())
        key=signature.hexdigest();path=self.cache_dir/(key+'.json');raw=None;cached=False;started=time.monotonic()
        if path.is_file():
            try:
                cache=json.loads(path.read_text(encoding='utf8'))
                if (cache.get('key')==key and isinstance(cache.get('answer'),str)
                    and cache.get('answer_sha256')==hashlib.sha256(cache['answer'].encode()).hexdigest()):raw=cache['answer'];cached=True
            except (ValueError,OSError):pass
        if raw is None:
            self._load()
            import torch
            content=[dict(type='image',image=im) for im in images]+[dict(type='text',text=prompt)]
            inputs=self.processor.apply_chat_template([dict(role='user',content=content)],tokenize=True,
                add_generation_prompt=True,return_dict=True,return_tensors='pt').to('cuda')
            with torch.inference_mode():ids=self.model.generate(**inputs,max_new_tokens=max_tokens,do_sample=False)
            raw=self.processor.batch_decode(ids[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)[0]
            self.cache_dir.mkdir(parents=True,exist_ok=True)
            value=dict(key=key,answer=raw,answer_sha256=hashlib.sha256(raw.encode()).hexdigest())
            # A crash cannot leave a valid-looking partial response in the cache.
            tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False),encoding='utf8');tmp.replace(path)
        record=dict(key=key,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),answer=raw,
                    cache_hit=cached,seconds=round(time.monotonic()-started,3))
        self.calls.append(record)
        return parse_answer(raw)

    def classify(self,image):
        preview=image.copy();preview.thumbnail((1280,1536))
        value=self._ask([preview],PAGE_PROMPT)
        if not valid_classification(value):raise ValueError('Nieprawidłowy opis rodzaju strony')
        return value

    def structured(self,image,rows):
        w,h=image.size
        data=[[i,[round(v/n*1000) for v,n in zip(r['box'],(w,h,w,h))],r['text']] for i,r in enumerate(rows)]
        prompt=STRUCTURED_PROMPT+'\n'+json.dumps(data,ensure_ascii=False,separators=(',',':'))
        preview=image.copy();preview.thumbnail((1280,1536))
        return self._ask([preview],prompt,1800)

    def region_role(self,image,bubble):
        bounds=padded_box(pixel_box(bubble,image.size),*image.size,.12,minimum=12)
        crop=image.crop(bounds);crop.thumbnail((900,900));whole=image.copy();whole.thumbnail((1024,1280))
        return self._ask([whole,crop],ROLE_PROMPT)

    def review(self,image,document,checker):
        if document.get('review',{}).get('verified'):return document
        original=copy.deepcopy(document);self.calls=[];started=time.monotonic();changes=[]
        try:
            classification=self.classify(image);kind=classification['kind'];result=document['result'];analysis=document['analysis']
            # Credits and illustrations can contain story headings or tiny
            # utterances. They NEVER authorize deleting an entire page.
            if kind in {'cover_gallery','advertisement'} and classification['contains_readable_story'] is False:
                removed=[b['id'] for b in result['bubbles']]
                if removed:renumber_after_omission(document,removed);changes.append(dict(kind='editorial-page',removed=removed))
            elif kind=='character_profile':
                rows=sorted(checker.locate_context(image),key=lambda r:(r['box'][1],r['box'][0]))
                if len({field(r['text']) for r in rows if field(r['text'])})>=3:
                    plan=self.structured(image,rows);groups=layout(rows,plan,image.size,result['direction'])
                    if groups:
                        result['bubbles']=[dict(rectangle(g['box'],*image.size,min(r['score'] for r in g['rows']),'text',margin=6),
                            id=f'b{i+1}',order=i+1,panel_id=None) for i,g in enumerate(groups)]
                        result['confidence']=sum(b['confidence'] for b in result['bubbles'])/len(groups)
                        analysis['reading_anchors']={b['id']:{k:b[k] for k in ('x','y','w','h')} for b in result['bubbles']}
                        changes.append(dict(kind='structured-profile',groups=groups,ocr=rows,plan=plan))
            else:
                checks={v['region_id']:v.get('ocr',[]) for v in analysis.get('text_check',{}).get('regions',[])}
                removed=[];evidence=[]
                for b in result['bubbles']:
                    anchor=analysis.get('reading_anchors',{}).get(b['id'],b);ocr=checks.get(b['id'],[])
                    if region_candidate(b,anchor,ocr):
                        role=self.region_role(image,b)
                        if omission_allowed(role,ocr):removed.append(b['id']);evidence.append(dict(id=b['id'],classification=role,ocr=ocr))
                if removed:
                    mapping=renumber_after_omission(document,removed);changes.append(dict(kind='non-story-regions',removed=removed,preserved=mapping,evidence=evidence))
                if kind in {'mixed','story_recap'}:
                    rows=sorted(checker.locate_context(image),key=lambda r:(r['box'][1],r['box'][0]))
                    plan=self.structured(image,rows);groups=prose_groups(rows,plan,image.size);added=[]
                    for g in groups:
                        if any(intersection(g['box'],pixel_box(b,image.size))/max(1,area(g['box']))>.6 for b in result['bubbles']):continue
                        added.append(rectangle(g['box'],*image.size,min(r['score'] for r in g['rows']),'text',margin=6))
                    if added:
                        bubbles=result['bubbles'];anchors=analysis.get('reading_anchors',{})
                        for b in bubbles:b['_reading_box']=dict(anchors.get(b['id'],{k:b[k] for k in ('x','y','w','h')}))
                        bubbles.extend(added);saved={id(b):{k:b.get('_reading_box',b)[k] for k in ('x','y','w','h')} for b in bubbles}
                        document['result']=ordered_result(result['panels'],bubbles,*image.size,result['direction'],result.get('layout','auto'))
                        analysis['reading_anchors']={b['id']:saved[id(b)] for b in document['result']['bubbles']}
                        changes.append(dict(kind='recovered-prose',groups=groups,ocr=rows,plan=plan))
            changed=document['result']!=original['result']
            if changed:
                # All existing model diagnostics stay in the original snapshot.
                # Review newly constructed crops rather than reusing old IDs.
                document['analysis']['text_check']={'mode':'review','regions':[]}
                document['review']['flags']=[f for f in document['review']['flags'] if 'OCR nie potwierdził tekstu w regionie' not in f]
                checker.review(image,document)
                document['review']['verified']=False
                document['review']['flags'].append('Analiza kontekstu zmieniła listę czytania; sprawdź wynik. Poprzednie wykrycia można przywrócić jednym przyciskiem')
            document['analysis']['page_context']=dict(status='applied' if changed else 'unchanged',classification=classification,
                model=self.provenance,calls=self.calls,changes=changes,seconds=round(time.monotonic()-started,3))
            if changed:document['analysis']['page_context']['original']=original
            return document
        except Exception as error:
            if self.strict:raise
            original['analysis']['page_context']=dict(status='unavailable',error=type(error).__name__,model=self.provenance)
            original['review']['flags'].append('Analiza kontekstu była niedostępna; zachowano wynik detektorów do kontroli')
            return original


def restore_page_context(document):
    audit=document.get('analysis',{}).get('page_context',{})
    if audit.get('status')!='applied' or not audit.get('original'):return False
    original=copy.deepcopy(audit['original']);record={k:v for k,v in audit.items() if k!='original'};record['status']='restored'
    document.clear();document.update(original);document['analysis']['page_context']=record;document['review']['verified']=False
    return True
