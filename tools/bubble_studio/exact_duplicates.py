"""Remove only fully identical geometry and identical immutable reading anchors."""
import copy
from .quality_metrics import geometry_digest
from .page_context import renumber_after_omission

def remove_exact_duplicates(document):
 if document.get('review',{}).get('verified'):return document
 anchors=document['analysis'].get('reading_anchors',{});seen={};removed=[]
 for bubble in document['result']['bubbles']:
  anchor=anchors.get(bubble['id'])
  if not anchor:continue
  key=(geometry_digest(bubble),tuple(anchor.get(k) for k in ('x','y','w','h')),bubble.get('panel_id'))
  if key in seen:removed.append(bubble['id'])
  else:seen[key]=bubble['id']
 if removed:
  original=copy.deepcopy(document);mapping=renumber_after_omission(document,removed)
  document['analysis']['exact_duplicate_removal']=dict(original=original,removed=removed,mapping=mapping)
  document['review']['flags'].append('Usunięto identyczny duplikat tego samego obszaru czytania')
 return document
