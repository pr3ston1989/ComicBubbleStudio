"""Scene audit with per-page rollback and strictly serialized GPU models."""
import copy
from .retail_promotion import refine as retail
from .scene_objects import refine as objects
from .compound_guard import recover_compounds
from .native_enclosures import enclosure_candidates
from .scene_gutters import refine_gutter_order
def refine_page(image,document,checker,semantic,scene):
 if checker is None or semantic is None or scene is None or document.get('review',{}).get('verified'):return document
 original=copy.deepcopy(document)
 try:
  document=retail(image,document,semantic)
  semantic.park()
  document=objects(image,document,scene)
  document=refine_gutter_order(image,document,scene)
  scene.park()
  document=recover_compounds(image,document,checker,proposal_factory=lambda image,doc:enclosure_candidates(image,doc,trim_blank=True))
 except Exception as error:
  if getattr(semantic,'strict',False) or getattr(scene,'strict',False):raise
  document=original
  document['analysis']['refinement260_error']=type(error).__name__
  document['review']['flags'].append('Dodatkowa analiza scen była niedostępna; zachowano poprzedni wynik')
 finally:
  semantic.park();scene.park()
 if document['result']!=original['result']:
  document['analysis']['scene_refinement']=dict(original=original,model=scene.provenance)
  context=document['analysis'].setdefault('page_context',{});context.setdefault('original',original);context['status']='applied'
  context.setdefault('changes',[]).append(dict(kind='scene-refinement-260'))
 return document
