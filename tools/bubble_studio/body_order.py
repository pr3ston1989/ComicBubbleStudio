"""Use complete balloon bodies for unambiguous within-panel reading rows."""
import copy
import re
from web.backend.comic_smartview_layout import order_boxes_in_rows
from .strip_reader import _body_anchor


def _overlap(a,b):
    hit=max(0,min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']))*max(0,min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y']))
    return hit/max(1e-9,min(a['w']*a['h'],b['w']*b['h']))


def refine_body_order(image,document):
    if document.get('review',{}).get('verified'):return document
    original=copy.deepcopy(document);result=document['result'];bubbles=result['bubbles']
    anchors=document['analysis'].get('reading_anchors',{})
    if set(anchors)!={b['id'] for b in bubbles}:return document
    identities={id(b):b['id'] for b in bubbles}
    for panel in result['panels']:
        indices=[i for i,b in enumerate(bubbles) if b.get('panel_id')==panel['id']]
        group=[bubbles[i] for i in indices]
        if len(group)<2 or any(b.get('type')!='bubble' or not b.get('polygons') for b in group):continue
        # Joined lobes and nested/duplicate detections keep their established
        # stricter order. A large bounding box cannot authorize reordering its
        # neighbouring speakers through the empty space between the lobes.
        if any(_overlap(a,b)>.8 for n,a in enumerate(group) for b in group[n+1:]):continue
        proxies=[_body_anchor(image,b,anchors[b['id']],panel) for b in group]
        if any(a['y']==anchors[b['id']]['y'] and a['h']==anchors[b['id']]['h'] for a,b in zip(proxies,group)):continue
        originals={id(a):b for a,b in zip(proxies,group)}
        ordered=[originals[id(a)] for a in order_boxes_in_rows(proxies,result['direction'],align_starts=False)]
        for i,b in zip(indices,ordered):bubbles[i]=b
    mapping={identities[id(b)]:f'b{i+1}' for i,b in enumerate(bubbles)}
    if all(k==v for k,v in mapping.items()):return document
    for i,b in enumerate(bubbles):b.update(id=f'b{i+1}',order=i+1)
    document['analysis']['reading_anchors']={mapping[k]:v for k,v in anchors.items()}
    for row in document['analysis'].get('text_check',{}).get('regions',[]):row['region_id']=mapping[row['region_id']]
    document['review']['flags']=[re.sub(r'\bb\d+\b',lambda m:mapping.get(m[0],m[0]),s) for s in document['review']['flags']]
    audit=dict(kind='balloon-body-order',mapping=mapping)
    document['analysis']['body_order']=audit;context=document['analysis'].setdefault('page_context',{})
    context.setdefault('original',original);context['status']='applied';context.setdefault('changes',[]).append(audit)
    document['review']['flags'].append('Ustalono kolejność sąsiednich dymków na podstawie ich korpusów; sprawdź kolejność')
    return document
