"""Reversible, conservative final page checks; unavailable vision preserves input."""
import copy
from .nonstory_mask import refine as refine_nonstory


def refine_page(image,document,semantic):
 if semantic is None or document.get('review',{}).get('verified'):return document
 original=copy.deepcopy(document)
 try:
  document=refine_nonstory(image,document,semantic)
 except Exception as error:
  if getattr(semantic,'strict',False):raise
  document=original
  document['analysis']['refinement252_error']=type(error).__name__
  document['review']['flags'].append('Dodatkowa kontrola tekstów była niedostępna; zachowano dotychczasowy wynik')
 finally:
  if hasattr(semantic,'park'):semantic.park()
 if document['result']!=original['result']:
  context=document['analysis'].setdefault('page_context',{})
  context.setdefault('original',original);context['status']='applied'
  context.setdefault('changes',[]).append(dict(kind='nonstory-audit-252'))
 return document
