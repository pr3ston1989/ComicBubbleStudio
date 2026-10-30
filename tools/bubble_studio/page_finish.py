"""Conservative final reading and native-pixel refinements, in audited order."""
import copy
from .strip_reader import refine_strips
from .publishing_filter import refine_publishing
from .body_order import refine_body_order
from .compound_guard import recover_compounds
from .color_stroke_guard import recover_page_color_outlines
from .tail_continuation import continue_page_tails


def refine_semantic_page(image, document, checker, context):
    if document.get('review', {}).get('verified'):
        return document
    for stage in (refine_strips, refine_publishing):
        previous = copy.deepcopy(document)
        try:
            document = stage(image, document, checker, context)
        except Exception as error:
            if getattr(context, 'strict', False):
                raise
            document = previous
            document['analysis'].setdefault('final_context_failures', []).append(
                dict(stage=stage.__name__, error=type(error).__name__))
            document['review']['flags'].append(
                'Dodatkowa kontrola układu lub materiałów wydawniczych była niedostępna; zachowano wcześniejszy wynik')
    return document


def refine_native_page(image, document, checker):
    document = refine_body_order(image, document)
    document = recover_compounds(image, document, checker)
    document = recover_page_color_outlines(image, document)
    return continue_page_tails(image, document)
