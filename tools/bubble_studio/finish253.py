"""Recover independently confirmed unframed story text without modifying old stops."""
import copy
from .short_text import refine
from .panel_background import refine as repair_background


def refine_page(image,document,checker,semantic):
 if checker is None or semantic is None or document.get('review',{}).get('verified'):return document
 original=copy.deepcopy(document)
 try:
  document=refine(image,document,checker,semantic)
  document=repair_background(image,document)
 except Exception as error:
  if getattr(semantic,'strict',False):raise
  document=original
  document['analysis']['refinement253_error']=type(error).__name__
  document['review']['flags'].append('Dodatkowe odzyskiwanie tekstu było niedostępne; zachowano poprzedni wynik')
 finally:
  if hasattr(semantic,'park'):semantic.park()
 if document['result']!=original['result']:
  context=document['analysis'].setdefault('page_context',{})
  context.setdefault('original',original);context['status']='applied'
  context.setdefault('changes',[]).append(dict(kind='unframed-text-253'))
 return document
