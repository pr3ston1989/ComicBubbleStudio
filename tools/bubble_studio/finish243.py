"""Additional native refinements; previous inference stages remain unchanged."""
from .enclosure_repair import repair_page_enclosures
from .lobe_order import refine_lobe_order
from .thought_dots import recover_page_thought_dots


def refine_additional_page(image, document, checker):
    document = repair_page_enclosures(image, document, checker)
    document = refine_lobe_order(image, document)
    return recover_page_thought_dots(image, document)
