"""Constrained OCR layout: model hints cannot merge independent profile fields."""
import copy
import re
import math
import numpy as np
from .geometry import rectangle,intersection,area

FIELDS=('realname','height','weight','weapon','weapons','employer','company','biography','funfact','classification','territory','temperament','threatlevel','description','humanrecord')

def field(text):
 s=re.sub('[^a-z]','',text.lower())
 return next((w for w in sorted(FIELDS,key=len,reverse=True) if s.startswith(w)),None)

def layout(rows,plan,size,direction='ltr'):
 # Invalid geometry or hallucinated IDs cannot authorize a page replacement.
 if not valid_rows(rows,size):return []
 if not valid_plan(plan,len(rows)):plan=None
 rows=copy.deepcopy(rows);w,h=size
 fields=[r for r in rows if field(r['text'])]
 if len({field(r['text']) for r in fields})<3:return []
 previews=[r for r in rows if re.sub('[^a-z]','',r['text'].lower())=='nextissue']
 if previews and sum(r['text'].count('?') for r in rows)>=6:
  rows=[r for r in rows if r['box'][1]<min(p['box'][1] for p in previews)]
 heights=[r['box'][3]-r['box'][1] for r in fields];median=float(np.median(heights));atoms=[]
 for i,r in enumerate(rows):
  r['indices']=[i];a,b,c,d=r['box'];target=None
  for other in reversed(atoms):
   u,v,x,y=other['box'];overlap=min(d,y)-max(b,v);gap=max(a,u)-min(c,x)
   if overlap>=.55*min(d-b,y-v) and gap<=1.75*max(d-b,y-v) and gap>=-.3*min(c-a,x-u):target=other;break
  if target:
   target['box']=[min(a,target['box'][0]),min(b,target['box'][1]),max(c,target['box'][2]),max(d,target['box'][3])];target['text']+=' '+r['text'];target['indices']+=r['indices']
  else:atoms.append(r)
 starts={g['lines'][0] for g in (plan or {}).get('groups',[]) if g.get('lines')}
 groups=[]
 for row in atoms:
  box=row['box'];height=box[3]-box[1];label=field(row['text']);heading=not label and height>median*1.6
  target=None
  if not label:
   for g in reversed(groups):
    p=g['rows'][-1];pb=p['box'];gap=box[1]-pb[3];xover=max(0,min(box[2],g['box'][2])-max(box[0],g['box'][0]))/max(1,min(box[2]-box[0],g['box'][2]-g['box'][0]))
    if xover<.5:continue
    if heading and g['heading']:
     if -.2*height<=gap<=.25*min(height,pb[3]-pb[1]):target=g
    elif not heading and not g['heading'] and gap<=1.6*median:
     target=g
     if len(g['rows'])>=3 and row['indices'][0] in starts:
      colwidth=max(r['box'][2]-r['box'][0] for r in atoms if abs(r['box'][0]-box[0])<2*median and not field(r['text']))
      if gap>=.8*median or ((box[2]-box[0])>=.85*colwidth and (re.search(r'[.!?]["\x27’”]*\s*$',p['text']) or pb[2]-pb[0]<.8*colwidth)):target=None
    break
  if target:
   target['rows'].append(row);target['box']=[min(target['box'][0],box[0]),min(target['box'][1],box[1]),max(target['box'][2],box[2]),max(target['box'][3],box[3])]
  else:groups.append(dict(rows=[row],box=box[:],field=label,heading=heading))
 groups=[g for g in groups if g['heading'] or g['field'] or len(g['rows'])>=2
         or sum(c.isalpha() for r in g['rows'] for c in r['text'])>=30]
 for g in groups:
  if g['heading']:continue
  # OCR can return only a fragment of an otherwise long printed line. A field
  # is a full column entry, so retain the stable extent of its text column,
  # including words missing from a shorter OCR fragment in this one paragraph.
  anchor=min(fields,key=lambda r:abs(r['box'][0]-g['box'][0]))['box'][0]
  column=[r for r in rows if abs(r['box'][0]-anchor)<2*median and r['box'][3]-r['box'][1]<1.6*median]
  if column:g['box'][0]=min(g['box'][0],min(r['box'][0] for r in column));g['box'][2]=max(g['box'][2],max(r['box'][2] for r in column))
 return order_profile_groups(groups,median,direction)


def valid_rows(rows,size):
 w,h=size
 return bool(rows) and all(isinstance(r.get('text'),str) and r.get('score',0)>=.85
     and len(r.get('box',[]))==4 and all(math.isfinite(v) for v in r['box'])
     and 0<=r['box'][0]<r['box'][2]<=w+.1 and 0<=r['box'][1]<r['box'][3]<=h+.1 for r in rows)


def valid_plan(plan,count):
 if not isinstance(plan,dict) or not isinstance(plan.get('groups'),list):return False
 used=[]
 for g in plan['groups']:
  if not isinstance(g,dict) or not isinstance(g.get('lines'),list) or not g['lines']:return False
  if any(type(i) is not int or not 0<=i<count for i in g['lines']):return False
  used+=g['lines']
 return bool(used) and len(used)==len(set(used))


def order_profile_groups(groups,line_height,direction):
 """Read whole side-by-side profiles, but upper cards before lower cards."""
 from web.backend.comic_smartview_layout import order_boxes_by_cuts
 columns=[]
 for g in sorted((g for g in groups if g['field']),key=lambda g:g['box'][0]):
  x=g['box'][0]
  if not columns or x-columns[-1]['x']>2*line_height:columns.append(dict(x=x,groups=[]))
 if len(columns)<2:return sorted(groups,key=lambda g:(g['box'][1],g['box'][0] if direction=='ltr' else -g['box'][0]))
 for g in groups:min(columns,key=lambda c:abs(c['x']-g['box'][0]))['groups'].append(g)
 slots=[]
 for c in columns:
  if not c['groups']:continue
  bounds=[min(g['box'][0] for g in c['groups']),min(g['box'][1] for g in c['groups']),max(g['box'][2] for g in c['groups']),max(g['box'][3] for g in c['groups'])]
  slots.append(dict(x=bounds[0],y=bounds[1],w=bounds[2]-bounds[0],h=bounds[3]-bounds[1],groups=c['groups']))
 return [g for slot in order_boxes_by_cuts(slots,direction) for g in sorted(slot['groups'],key=lambda g:g['box'][1])]


def prose_groups(rows,plan,size):
 """Positive recap proposals must be coherent, spatially separate prose.

 Column separation and sentence case remove credit rows accidentally included
 by the language model. Its exclusion list never grants permission to delete.
 """
 if not valid_rows(rows,size) or not valid_plan(plan,len(rows)):return []
 output=[]
 legal=('allrightsreserved','noportionofthispublication','reproducedortransmitted',
        'expresswrittenpermission','productoftheauthor','digitalversion')
 for proposal in plan['groups']:
  if proposal.get('role')!='narration':continue
  selected=[]
  for i in proposal['lines']:
   r=rows[i];letters=[c for c in r['text'] if c.isalpha()]
   if len(letters)>=5 and sum(c.islower() for c in letters)/len(letters)>=.15:selected.append(r)
  columns=[]
  for r in sorted(selected,key=lambda r:r['box'][0]):
   target=next((c for c in columns if max(0,min(c['box'][2],r['box'][2])-max(c['box'][0],r['box'][0]))
       /max(1,min(c['box'][2]-c['box'][0],r['box'][2]-r['box'][0]))>=.65),None)
   if target:
    target['rows'].append(r);a,b,c,d=target['box'];u,v,x,y=r['box'];target['box']=[min(a,u),min(b,v),max(c,x),max(d,y)]
   else:columns.append(dict(rows=[r],box=r['box'][:]))
  if not columns:continue
  group=max(columns,key=lambda c:len(c['rows']));text=re.sub('[^a-z]','',' '.join(r['text'] for r in group['rows']).lower())
  if (len(group['rows'])<3 or len(text)<100 or len(group['rows'])<.6*max(1,len(selected))
      or group['box'][2]-group['box'][0]>.8*size[0] or any(word in text for word in legal)):continue
  output.append(group)
 return sorted(output,key=lambda g:(g['box'][1],g['box'][0]))
