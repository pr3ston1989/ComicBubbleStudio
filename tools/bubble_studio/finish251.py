"""Incremental refinements; no previous inference stages are changed."""
import copy
from .native_body import recover_page_bodies
from .exact_duplicates import remove_exact_duplicates
from .editorial_audit import refine_editorial,refine_publishing_regions
from .panel_gutters import refine_gutter_order
from .promotion_audit import refine_promotion

def refine_page(image,document,checker,semantic):
 if document.get('review',{}).get('verified'):return document
 original=copy.deepcopy(document)
 document=recover_page_bodies(image,document,checker,semantic)
 document=remove_exact_duplicates(document)
 if semantic is not None:
  try:
   for stage in (refine_editorial,refine_promotion,refine_publishing_regions,refine_gutter_order):
    try:document=stage(image,document,semantic)
    except Exception as error:
     if getattr(semantic,'strict',False):raise
     document['analysis']['refinement251_error']=type(error).__name__
     document['review']['flags'].append('Dodatkowa kontrola kontekstu była niedostępna; zachowano dotychczasowe wykrycia')
     break
  finally:
   if hasattr(semantic,'park'):semantic.park()
 if document['result']!=original['result']:
  context=document['analysis'].setdefault('page_context',{})
  context.setdefault('original',original);context['status']='applied'
  context.setdefault('changes',[]).append(dict(kind='native-and-editorial-251'))
 return document
