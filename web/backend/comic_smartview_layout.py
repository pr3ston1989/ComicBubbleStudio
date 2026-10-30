"""Geometria i kolejność czytania kadrów oraz dymków.

Modul jest celowo wolny od Pillow i numpy: przyjmuje gotowe prostokaty oraz
funkcje szukajace przerw miedzy kadrami, dzieki czemu cala logika kolejnosci
daje sie przetestowac bez generowania obrazow.

Kluczowa decyzja projektowa: kolejnosc czytania wynika z **drzewa ciec**, a nie
z ponownego sortowania wspolrzednych. Rekurencyjne ciecie strony i tak buduje
strukture, ktora dokladnie odwzorowuje sposob czytania, wiec wystarczy przejsc
ja w odpowiedniej kolejnosci dzieci. Wyprowadzanie kolejnosci z samych
wspolrzednych psuje sie na ukladzie „wysoki kadr obok dwoch spietrzonych”,
bardzo czestym w mandze.
"""

from __future__ import annotations

from typing import Callable, Iterable, Literal, Sequence

Region = tuple[int, int, int, int]
Axis = Literal["row", "column"]
Direction = Literal["ltr", "rtl"]

#: Uklad kadrow na stronie. Rozstrzyga kolejnosc tam, gdzie geometria jest
#: dwuznaczna.
#:
#: Strona 4-koma i zachodnia siatka 2xN maja **identyczna** geometrie: czysty
#: podzial na obu osiach. Roznica jest kulturowa, nie mierzalna — w 4-koma czyta
#: sie cale paski, w siatce wiersze. Zadna heurystyka tego nie rozstrzygnie
#: pewnie, dlatego `auto` zgaduje po szerokosci rynny, a uzytkownik moze narzucic
#: odpowiedz. Tak samo dziala comiXology, gdzie kolejnosc ustawiaja redaktorzy.
#:
#: rows    — pasami z gory na dol, w pasie zgodnie z kierunkiem
#: columns — calymi paskami pionowymi; pierwszy pasek od prawej przy rtl
#: single  — cala strona jako jeden przystanek (plansze)
PanelLayout = Literal["auto", "rows", "columns", "single"]
GutterFinder = Callable[[Region, Axis], list[tuple[int, int]]]

MAX_SPLIT_DEPTH = 7


def split_region_in_reading_order(
    region: Region,
    find_gutters: GutterFinder,
    direction: Direction,
    minimum_area: float,
    depth: int = 0,
) -> list[Region]:
    """Podziel obszar rekurencyjnie i zwroc kadry od razu w kolejnosci czytania.

    Ciecia poziome maja pierwszenstwo przed pionowymi. Przerwa pozioma jest
    wykrywana tylko wtedy, gdy biegnie przez cala szerokosc obszaru, wiec jej
    obecnosc oznacza prawdziwy pas kadrow — a komiks czyta sie pasami.
    Gdyby najpierw ciac pionowo, siatka 2x2 zostalaby przeczytana kolumnami.
    """
    left, top, right, bottom = region
    area = (right - left) * (bottom - top)
    if depth >= MAX_SPLIT_DEPTH or area < minimum_area * 2:
        return [region]

    axis, cut = _best_cut(region, find_gutters)
    if axis is None or cut is None:
        return [region]

    start, end = cut
    if axis == "row":
        children = [(left, top, right, top + start), (left, top + end, right, bottom)]
    else:
        children = [(left, top, left + start, bottom), (left + end, top, right, bottom)]
        # Manga czyta kolumny od prawej, wiec prawe dziecko idzie pierwsze.
        if direction == "rtl":
            children.reverse()

    if any((x2 - x1) * (y2 - y1) < minimum_area for x1, y1, x2, y2 in children):
        return [region]

    ordered: list[Region] = []
    for child in children:
        ordered.extend(
            split_region_in_reading_order(child, find_gutters, direction, minimum_area, depth + 1)
        )
    return ordered


def _best_cut(region: Region, find_gutters: GutterFinder) -> tuple[Axis | None, tuple[int, int] | None]:
    """Najszersza przerwa pozioma, a gdy takiej nie ma — najszersza pionowa."""
    for axis in ("row", "column"):
        gutters = find_gutters(region, axis)  # type: ignore[arg-type]
        if gutters:
            widest = max(gutters, key=lambda run: run[1] - run[0])
            return axis, widest  # type: ignore[return-value]
    return None, None


def order_boxes_in_rows(
    boxes: Sequence[dict],
    direction: Direction,
    minimum_overlap: float = 0.25,
    align_starts: bool = True,
) -> list[dict]:
    """Uszereguj prostokaty pasami: z gory na dol, w pasie zgodnie z kierunkiem.

    Pas definiuje **pionowe zachodzenie na kotwice**, a nie prog liczbowy na
    wspolrzednej y. Dwa dymki obok siebie na podobnej wysokosci zachodza na
    siebie w pionie, a dymek wyraznie nizej — nie. Regula nie ma parametru
    zaleznego od skali strony i nie psuje sie, gdy jeden element jest znacznie
    wyzszy od reszty. Porownanie tylko z kotwica zapobiega lancuchowemu
    sklejaniu calej kolumny w jeden pas.
    """
    if not boxes:
        return []
    remaining = sorted(boxes, key=lambda box: (box["y"], box["x"]))
    ordered: list[dict] = []
    while remaining:
        anchor = remaining[0]
        row = [box for box in remaining if _overlaps_vertically(anchor, box, minimum_overlap, align_starts)]
        row.sort(key=lambda box: box["x"], reverse=direction == "rtl")
        ordered.extend(row)
        consumed = {id(box) for box in row}
        remaining = [box for box in remaining if id(box) not in consumed]
    return ordered


#: Ile razy szersza musi byc rynna pionowa od poziomej, by ciac najpierw w pionie.
#:
#: Rozstrzyga uklad 4-koma: strona z dwoma paskami po cztery kadry ma czysty
#: podzial na OBU osiach, a wynik zalezy od tego, ktora wybierzemy. Ciecie pasami
#: daje zygzak miedzy dwoma osobnymi dowcipami (zmierzone na Azumanga s.575:
#: kolejnosc 1 prawy-gora, 2 lewy-gora, 3 prawy-2, 4 lewy-2...), a ciecie
#: kolumnami daje poprawne 1-4 w prawym pasku i 5-8 w lewym.
#:
#: Rozroznieniem jest szerokosc rynny: w 4-koma rynna miedzy paskami jest wyrazna
#: (zmierzone na Azumanga s.575: okolo 130 px wobec 64 px miedzy wierszami), a w
#: zwyklym komiksie rynny sa rowne. Przy rownych wygrywa pas, bo tak czyta sie
#: siatke 2x2. Prog 1.5 zostawia zapas na nierownosci skanu.
COLUMN_FIRST_GUTTER_RATIO = 1.5


#: Ponizej tego pokrycia strony kadrami mamy siatke miniatur, nie kadry historii.
#: Zmierzone na 23 opisanych recznie stronach: galeria okladek i reklama zajmuja
#: 26-38% strony, bo maja szerokie marginesy na podpisy, a pasek 4-koma 64-70%.
EXTRA_PAGE_COVERAGE = 0.45

#: Rozrzut wielkosci kadrow NIE jest juz warunkiem. Zostaje jako opis pomiaru.
#:
#: Pierwotnie regula wymagala takze rownomiernych kadrow (rozrzut ponizej 0.05),
#: bo galeria miniatur ma je rowne. Warunek okazal sie krucha: po obnizeniu progu
#: pewnosci kadrow model znalazl na stronie reklamy Vampirella s.022 dziewiec
#: kadrow o roznych rozmiarach i rozrzut wzrosl z 0.02 na 0.11, wiec strona
#: przestala byc rozpoznawana jako dodatek i dostawala dziewiec przystankow.
#:
#: Pokrycie strony rozdziela te przypadki samo: dodatki zajmuja 30-38%, a pasek
#: 4-koma bez dialogu 69.6%. Dodatkowy warunek tylko psul wynik przy zmianie
#: czulosci detektora.
MEASURED_EXTRA_PAGE_SPREAD = 0.11


def classify_page_kind(
    frames: int,
    balloons: int,
    coverage: float,
    spread: float,
) -> Literal["story", "extra"]:
    """Czy strona nalezy do historii, czy jest dodatkiem.

    Uklad kadrow jest cecha tytulu, ale rodzaj strony zmienia sie w jego wnetrzu:
    okladka, galeria okladek wariantowych, reklama, indeks. Ustawienie per tytul
    ich nie rozroznia, wiec potrzebna jest regula.

    Zmierzone na 23 stronach opisanych recznie po ogladzie: regula wskazuje 8 z 9
    dodatkow i **ani jednej** z 14 stron fabularnych. Nierozpoznany przypadek to
    plansza calostronicowa z creditsami, ktora ma dwa dymki — a skoro ma dymki, to
    prowadzenie po nich niczego nie psuje.

    Brak dymkow jest warunkiem koniecznym, bo strona z dialogiem zawsze nalezy do
    historii. Sam brak nie wystarcza: cicha strona akcji i pasek 4-koma bez kwestii
    tez nie maja dymkow.
    """
    if balloons > 0:
        return "story"
    if frames == 0:
        # Okladka, indeks, plansza bez ramek — nie ma po czym prowadzic.
        return "extra"
    del spread  # Zmierzone jako niewiarygodne, patrz MEASURED_EXTRA_PAGE_SPREAD.
    if coverage < EXTRA_PAGE_COVERAGE:
        return "extra"
    return "story"


def order_boxes_by_cuts(
    boxes: Sequence[dict],
    direction: Direction,
    page_aspect: float = 1.0,
    layout: PanelLayout = "auto",
    depth: int = 0,
) -> list[dict]:
    """Uszereguj prostokaty rekurencyjnym cieciem, jak strone komiksu.

    Dziala na samych prostokatach, bez obrazu: rynna to przerwa w rzucie kadrow na
    os, ktorej nie przecina zaden kadr. Rekurencja odwzorowuje sposob czytania,
    dlatego radzi sobie z ukladami, na ktorych sortowanie pasmami sie lamie —
    „wysoki kadr obok dwoch spietrzonych” i pasek 4-koma.

    `page_aspect` to wysokosc strony podzielona przez szerokosc. Jest konieczne,
    bo prostokaty sa znormalizowane osobno do szerokosci i wysokosci, wiec ta sama
    rynna w pikselach ma inna wartosc na kazdej osi. Bez tej poprawki strona
    3347x4800 z rownymi rynnami dawalaby iloraz 1.43 — o wlos od progu, ktorym
    rozstrzygamy uklad 4-koma.
    """
    if len(boxes) <= 1 or depth >= MAX_SPLIT_DEPTH:
        return list(boxes)

    rows, row_gap = _cluster_along(boxes, "y", "h")
    columns, column_gap = _cluster_along(boxes, "x", "w")

    if layout == "columns":
        prefer_columns = len(columns) > 1
    elif layout == "rows":
        prefer_columns = False
    else:
        # Porownanie w jednej jednostce: rynna pionowa mierzona wzdluz szerokosci,
        # pozioma wzdluz wysokosci.
        prefer_columns = (
            len(columns) > 1
            # Two diagonally separated balloons do not establish two strips.
            # With a real horizontal cut, require repeated vertical structure
            # in every column before inferring 4-koma from gutter width.
            and (len(rows) == 1 or all(len(column) >= 3 for column in columns))
            and column_gap > row_gap * page_aspect * COLUMN_FIRST_GUTTER_RATIO
        )

    if len(rows) > 1 and not prefer_columns:
        groups = rows
    elif len(columns) > 1:
        groups = columns
        # Manga czyta kolumny od prawej.
        if direction == "rtl":
            groups.reverse()
    else:
        # Kadry zachodza na siebie na obu osiach — zostaje sortowanie pasmami.
        return order_boxes_in_rows(boxes, direction)

    # Wymuszony uklad obowiazuje tylko na najwyzszym poziomie. Wewnatrz paska
    # kadry czyta sie juz normalnie z gory na dol, inaczej „paski pionowe”
    # rozbijalyby kazdy kadr na kolumny w nieskonczonosc.
    nested: PanelLayout = "auto" if layout == "columns" else layout
    ordered: list[dict] = []
    for group in groups:
        ordered.extend(order_boxes_by_cuts(group, direction, page_aspect, nested, depth + 1))
    return ordered


def _cluster_along(
    boxes: Sequence[dict],
    start_key: str,
    size_key: str,
) -> tuple[list[list[dict]], float]:
    """Rozbij prostokaty na grupy rozdzielone przerwami na jednej osi.

    Zwraca grupy w kolejnosci rosnacej wspolrzednej oraz **najwezsza** przerwe
    miedzy grupami. Najwezsza, a nie najszersza, bo to ona decyduje, czy podzial
    jest wyrazny na calej osi.
    """
    ordered = sorted(boxes, key=lambda box: box[start_key])
    groups: list[list[dict]] = [[ordered[0]]]
    gaps: list[float] = []
    reach = ordered[0][start_key] + ordered[0][size_key]

    for box in ordered[1:]:
        if box[start_key] > reach:
            gaps.append(box[start_key] - reach)
            groups.append([box])
            reach = box[start_key] + box[size_key]
            continue
        groups[-1].append(box)
        reach = max(reach, box[start_key] + box[size_key])

    return groups, min(gaps) if gaps else 0.0


def _overlaps_vertically(anchor: dict, box: dict, minimum_overlap: float, align_starts: bool = True) -> bool:
    """Czy prostokat dzieli z kotwica dosc wysokosci, by czytac je jako jeden pas."""
    if box is anchor:
        return True
    overlap = min(anchor["y"] + anchor["h"], box["y"] + box["h"]) - max(anchor["y"], box["y"])
    if overlap <= 0:
        return False
    # A tall/slanted frame can overlap the row below in its bounding box.
    # Shared pixels alone must not absorb much lower panels into its top row.
    if align_starts and abs(anchor['y']-box['y']) > .5*min(anchor['h'],box['h']):
        return False
    return overlap >= minimum_overlap * min(anchor["h"], box["h"])


def renumber(boxes: Iterable[dict], prefix: str) -> list[dict]:
    """Nadaj stabilne identyfikatory i kolejnosc 1..n zgodnie z lista wejsciowa."""
    result = []
    for index, box in enumerate(boxes, start=1):
        box["id"] = f"{prefix}{index}"
        box["order"] = index
        result.append(box)
    return result


#: Minimalny udzial dymka w kadrze, by rozwazyc przypisanie, gdy srodek wypadl obok.
#: Nisko, bo dymek przechodzacy przez rynne dzieli sie miedzy kadry niemal po
#: polowie — zmierzony przypadek mial 49.7% w jednym z nich. Prog ma tylko odsiac
#: kadry ledwie musniete narozem, a nie rozstrzygac remisy.
MINIMUM_PANEL_SHARE = 0.25


def containing_panel(panels: Sequence[dict], box: dict) -> dict | None:
    """Kadr, do ktorego nalezy prostokat.

    Podstawowa regula to srodek wewnatrz kadru. Sam srodek jednak zawodzi na
    wlos: zmierzony przypadek to dymek o srodku na 49.65% szerokosci przy kadrze
    zaczynajacym sie na 49.7%. Taki dymek przechodzi przez rynne i lezy w kadrze
    niemal dokladnie w polowie, a wypadal z niego calkiem. Dlatego przy braku
    trafienia srodkiem wybieramy kadr o najwiekszym udziale dymka.
    """
    center_x = box["x"] + box["w"] / 2
    center_y = box["y"] + box["h"] / 2
    matches = [
        panel for panel in panels
        if panel["x"] <= center_x <= panel["x"] + panel["w"]
        and panel["y"] <= center_y <= panel["y"] + panel["h"]
    ]
    if matches:
        return min(matches, key=lambda panel: panel["w"] * panel["h"])

    best = None
    best_share = MINIMUM_PANEL_SHARE
    for panel in panels:
        share = _covered_share(box, panel)
        if share > best_share:
            best, best_share = panel, share
    return best


def _covered_share(box: dict, panel: dict) -> float:
    """Jaka czesc `box` lezy wewnatrz `panel`."""
    overlap_w = min(box["x"] + box["w"], panel["x"] + panel["w"]) - max(box["x"], panel["x"])
    overlap_h = min(box["y"] + box["h"], panel["y"] + panel["h"]) - max(box["y"], panel["y"])
    if overlap_w <= 0 or overlap_h <= 0:
        return 0.0
    area = box["w"] * box["h"]
    return (overlap_w * overlap_h) / area if area > 0 else 0.0


def _staggered_text_group(boxes: Sequence[dict]) -> bool:
    """Three or more separate text blocks form a descending staircase.

    Unlike adjacent columns that start together, these paragraphs have clearly
    staggered starts and progress consistently to one side. Vertical overlap of
    their lower lines must not turn the whole staircase into an RTL/LTR row.
    Require the pattern across the whole group; mixed balloons remain on the
    established row rule for short replies beside long speeches.
    """
    if len(boxes)<3 or any(b.get('type')!='text' for b in boxes):
        return False
    ordered=sorted(boxes,key=lambda b:b['y'])
    shifts=[]
    for a,b in zip(ordered,ordered[1:]):
        if b['y']-a['y']<=.5*min(a['h'],b['h']):
            return False
        shift=(b['x']+b['w']/2)-(a['x']+a['w']/2)
        if abs(shift)<=.15*min(a['w'],b['w']):
            return False
        shifts.append(shift)
    return all(s>0 for s in shifts) or all(s<0 for s in shifts)


def group_bubbles_by_panel(
    panels: Sequence[dict],
    bubbles: Sequence[dict],
    direction: Direction,
    page_aspect: float = 1.0,
    layout: PanelLayout = "auto",
) -> list[dict]:
    """Ustaw dymki w kolejnosci czytania: kadr po kadrze, w kadrze pasami.

    Dymek bez kadru staje sie wlasnym przystankiem i jest wplatany wedlug swojego
    miejsca na stronie. Dopisywanie sierot na koniec bylo zle: na stronach, gdzie
    kadry nie maja ramek i model znajduje ich niewiele, wieksza czesc dymkow jest
    sierotami i kolejnosc przestaje mieć zwiazek ze strona. Zmierzony przypadek to
    Astro City 008 s.6, gdzie narracja z samej gory strony byla czytana jako
    siodma i osma pozycja.
    """
    slots: list[dict] = []
    # Undetected top frames/narration must finish before the detected lower
    # grid. Treating each top utterance as a thin full-page column can interleave
    # it with several rows of panels, especially on a 3-column Western page.
    first_panel_y=min((p['y'] for p in panels),default=0)
    leading=[b for b in bubbles if not b.get('panel_id') and b['y']+b['h']<=first_panel_y]
    leading_ids={id(b) for b in leading}
    for panel in panels:
        group = [bubble for bubble in bubbles if bubble.get("panel_id") == panel["id"]]
        # Silent panels still constrain the page's gutters. Dropping them can
        # turn two sparse utterances into false columns and reverse page order.
        # Text paragraphs in the same panel can have very different heights.
        # The start-alignment constraint is for frames; applying it to text can
        # put a long paragraph before a short reply on its reading side.
        # Nested text anchors are evidence of a duplicate or merged detection.
        # Keep the stricter existing order in this ambiguous group so relaxing
        # the row rule cannot read an inner duplicate ahead of its outer text.
        nested=any(b.get('_layout_ambiguous') for b in group) or any(_covered_share(a,b)>.8 or _covered_share(b,a)>.8
                   for i,a in enumerate(group) for b in group[i+1:])
        slots.append({"box": panel, "bubbles": order_boxes_in_rows(group, direction,
                      align_starts=nested or _staggered_text_group(group))})
    for bubble in bubbles:
        if not bubble.get("panel_id") and id(bubble) not in leading_ids:
            slots.append({"box": bubble, "bubbles": [bubble]})

    by_box = {id(slot["box"]): slot for slot in slots}
    ordered: list[dict] = order_boxes_in_rows(leading,direction,align_starts=False)
    # Przystanki ida tym samym cieciem co kadry: na stronie 4-koma sortowanie
    # pasmami przeplatalo dymki z dwoch osobnych paskow.
    for box in order_boxes_by_cuts(
        [slot["box"] for slot in slots], direction, page_aspect, layout,
    ):
        ordered.extend(by_box[id(box)]["bubbles"])
    return ordered


def inset_box(box: tuple[int, int, int, int], ratio: float, minimum: int = 2) -> tuple[int, int, int, int]:
    """Zwez prostokat proporcjonalnie, by pominac ramke kadru lub obwodke dymka."""
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    pad_x = max(minimum, round(width * ratio))
    pad_y = max(minimum, round(height * ratio))
    if width - 2 * pad_x < 2 or height - 2 * pad_y < 2:
        return box
    return (left + pad_x, top + pad_y, right - pad_x, bottom - pad_y)


def deduplicate_boxes(boxes: Sequence[dict], overlap: float = 0.62) -> list[dict]:
    """Usun prostokaty mocno pokrywajace sie z pewniejszym kandydatem.

    Detekcja jasnych i ciemnych dymkow moze trafic w ten sam obszar (np. dymek
    o odwroconej palecie), wiec zostawiamy wariant o wyzszej pewnosci.
    """
    kept: list[dict] = []
    for box in sorted(boxes, key=lambda item: item.get("confidence", 0), reverse=True):
        if any(_intersection_ratio(box, other) >= overlap for other in kept):
            continue
        kept.append(box)
    return kept


def _intersection_ratio(a: dict, b: dict) -> float:
    """Udzial czesci wspolnej w mniejszym z prostokatow."""
    overlap_w = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
    overlap_h = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
    if overlap_w <= 0 or overlap_h <= 0:
        return 0.0
    smaller = min(a["w"] * a["h"], b["w"] * b["h"])
    return (overlap_w * overlap_h) / smaller if smaller > 0 else 0.0
