"""Kolejnosc czytania kadrow i dymkow.

Testy operuja na sztucznych przerwach i prostokatach, bez generowania obrazow,
zeby oddzielic poprawnosc kolejnosci od jakosci detekcji pikseli.
"""

from __future__ import annotations

from web.backend.comic_smartview_layout import (
    containing_panel,
    deduplicate_boxes,
    group_bubbles_by_panel,
    inset_box,
    classify_page_kind,
    order_boxes_by_cuts,
    order_boxes_in_rows,
    renumber,
    split_region_in_reading_order,
)


def box(x, y, w, h, **extra):
    return {"x": x, "y": y, "w": w, "h": h, **extra}


def gutters_from_map(mapping):
    """Zbuduj funkcje szukajaca przerw z jawnej mapy obszar -> przerwy."""
    def find(region, axis):
        return list(mapping.get((region, axis), []))
    return find


class TestPanelSplitReadingOrder:
    def test_horizontal_band_is_cut_before_vertical_column(self):
        """Siatka 2x2 musi byc czytana pasami, nie kolumnami.

        Gdy istnieje i przerwa pozioma, i pionowa, ciecie poziome ma
        pierwszenstwo — inaczej manga zostalaby przeczytana kolumnami.
        """
        page = (0, 0, 100, 100)
        top_row, bottom_row = (0, 0, 100, 45), (0, 55, 100, 100)
        find = gutters_from_map({
            (page, "row"): [(45, 55)],
            (top_row, "column"): [(45, 55)],
            (bottom_row, "column"): [(45, 55)],
        })

        panels = split_region_in_reading_order(page, find, "ltr", minimum_area=100)

        assert panels == [
            (0, 0, 45, 45), (55, 0, 100, 45),
            (0, 55, 45, 100), (55, 55, 100, 100),
        ]

    def test_rtl_reverses_only_the_column_order(self):
        page = (0, 0, 100, 100)
        top_row, bottom_row = (0, 0, 100, 45), (0, 55, 100, 100)
        find = gutters_from_map({
            (page, "row"): [(45, 55)],
            (top_row, "column"): [(45, 55)],
            (bottom_row, "column"): [(45, 55)],
        })

        panels = split_region_in_reading_order(page, find, "rtl", minimum_area=100)

        # Pasy nadal z gory na dol, ale w pasie od prawej do lewej.
        assert panels == [
            (55, 0, 100, 45), (0, 0, 45, 45),
            (55, 55, 100, 100), (0, 55, 45, 100),
        ]

    def test_tall_panel_beside_two_stacked_panels(self):
        """Uklad, na ktorym sortowanie po wspolrzednych sie wywraca.

        Wysoki kadr po prawej blokuje przerwe pozioma przez cala szerokosc,
        wiec strona dzieli sie najpierw pionowo. Dla mangi poprawna kolejnosc
        to: wysoki prawy, gorny lewy, dolny lewy.
        """
        page = (0, 0, 100, 100)
        left_column = (0, 0, 45, 100)
        find = gutters_from_map({
            (page, "column"): [(45, 55)],
            (left_column, "row"): [(45, 55)],
        })

        panels = split_region_in_reading_order(page, find, "rtl", minimum_area=100)

        assert panels == [
            (55, 0, 100, 100),   # wysoki kadr po prawej — czytany pierwszy
            (0, 0, 45, 45),      # gorny lewy
            (0, 55, 45, 100),    # dolny lewy
        ]

    def test_widest_gutter_wins_within_one_axis(self):
        page = (0, 0, 100, 100)
        find = gutters_from_map({(page, "row"): [(20, 24), (48, 60)]})

        panels = split_region_in_reading_order(page, find, "ltr", minimum_area=10)

        assert panels == [(0, 0, 100, 48), (0, 60, 100, 100)]

    def test_region_without_gutters_stays_whole(self):
        page = (0, 0, 100, 100)
        assert split_region_in_reading_order(page, gutters_from_map({}), "ltr", 100) == [page]

    def test_cut_producing_a_sliver_is_rejected(self):
        """Ciecie tworzace kadr mniejszy od progu zostawia obszar nietkniety."""
        page = (0, 0, 100, 100)
        find = gutters_from_map({(page, "row"): [(1, 3)]})

        assert split_region_in_reading_order(page, find, "ltr", minimum_area=500) == [page]

    def test_recursion_is_bounded(self):
        """Przerwa w kazdym obszarze nie moze zapetlic rekurencji."""
        find = lambda region, axis: [(1, 2)] if axis == "row" else []  # noqa: E731

        panels = split_region_in_reading_order((0, 0, 100, 10_000), find, "ltr", minimum_area=1)

        assert len(panels) <= 2 ** 7


class TestRowBandOrdering:
    def test_side_by_side_boxes_form_one_band(self):
        boxes = [box(0.6, 0.1, 0.2, 0.2), box(0.1, 0.12, 0.2, 0.2)]

        assert [b["x"] for b in order_boxes_in_rows(boxes, "ltr")] == [0.1, 0.6]
        assert [b["x"] for b in order_boxes_in_rows(boxes, "rtl")] == [0.6, 0.1]

    def test_clearly_lower_box_starts_a_new_band(self):
        boxes = [box(0.6, 0.5, 0.2, 0.2), box(0.1, 0.1, 0.2, 0.2)]

        assert [b["y"] for b in order_boxes_in_rows(boxes, "rtl")] == [0.1, 0.5]

    def test_one_tall_box_does_not_merge_two_bands(self):
        """Regresja: wysoki element nie moze skleic wszystkiego w jeden pas."""
        boxes = [
            box(0.05, 0.05, 0.2, 0.55, tag="tall"),
            box(0.4, 0.06, 0.2, 0.1, tag="top"),
            box(0.4, 0.45, 0.2, 0.1, tag="bottom"),
        ]

        tags = [b["tag"] for b in order_boxes_in_rows(boxes, "ltr")]

        # Wysoki i gorny czytamy razem, dolny dopiero potem.
        assert tags == ["tall", "top", "bottom"]

    def test_barely_touching_boxes_do_not_share_a_band(self):
        boxes = [box(0.1, 0.10, 0.2, 0.20, tag="upper"), box(0.5, 0.29, 0.2, 0.20, tag="lower")]

        assert [b["tag"] for b in order_boxes_in_rows(boxes, "ltr")] == ["upper", "lower"]

    def test_empty_input(self):
        assert order_boxes_in_rows([], "ltr") == []


class TestBubbleGrouping:
    def test_bubbles_follow_their_panel_then_orphans_last(self):
        panels = [box(0, 0, 0.5, 0.5, id="p1"), box(0.5, 0, 0.5, 0.5, id="p2")]
        bubbles = [
            box(0.55, 0.1, 0.1, 0.08, panel_id="p2", tag="in-p2"),
            box(0.05, 0.1, 0.1, 0.08, panel_id="p1", tag="in-p1"),
            box(0.2, 0.8, 0.1, 0.08, panel_id=None, tag="orphan"),
        ]

        tags = [b["tag"] for b in group_bubbles_by_panel(panels, bubbles, "ltr")]

        assert tags == ["in-p1", "in-p2", "orphan"]

    def test_smallest_containing_panel_wins(self):
        """Kadr w kadrze: dymek nalezy do wewnetrznego, nie do otaczajacego."""
        outer = box(0, 0, 1, 1, id="outer")
        inner = box(0.4, 0.4, 0.2, 0.2, id="inner")

        assert containing_panel([outer, inner], box(0.45, 0.45, 0.05, 0.05))["id"] == "inner"

    def test_box_outside_every_panel_has_no_parent(self):
        assert containing_panel([box(0, 0, 0.3, 0.3, id="p1")], box(0.8, 0.8, 0.1, 0.1)) is None


class TestHelpers:
    def test_renumber_assigns_sequential_ids_and_order(self):
        boxes = renumber([box(0, 0, 1, 1), box(0, 0, 1, 1)], "b")

        assert [b["id"] for b in boxes] == ["b1", "b2"]
        assert [b["order"] for b in boxes] == [1, 2]

    def test_inset_shrinks_proportionally(self):
        assert inset_box((0, 0, 100, 200), 0.1) == (10, 20, 90, 180)

    def test_inset_refuses_to_collapse_a_small_box(self):
        assert inset_box((0, 0, 4, 4), 0.4) == (0, 0, 4, 4)

    def test_deduplicate_keeps_the_more_confident_overlap(self):
        boxes = [
            box(0.1, 0.1, 0.2, 0.2, confidence=0.6, tag="weak"),
            box(0.11, 0.11, 0.2, 0.2, confidence=0.9, tag="strong"),
            box(0.7, 0.7, 0.2, 0.2, confidence=0.5, tag="separate"),
        ]

        tags = {b["tag"] for b in deduplicate_boxes(boxes)}

        assert tags == {"strong", "separate"}


class TestOrderByCuts:
    """Kolejnosc czytania z rekurencyjnego ciecia prostokatow.

    Zmierzone na Azumanga s.575: osiem poprawnie wykrytych kadrow 4-koma bylo
    czytane pasami, czyli 1 prawy-gora, 2 lewy-gora, 3 prawy-2, 4 lewy-2 — dwa
    osobne dowcipy naprzemiennie. Ciecie rozstrzyga to poprawnie.
    """

    #: Zmierzone na Azumanga Daioh s.575: strona 3347x4800, rynna miedzy paskami
    #: okolo 130 px, przerwy miedzy wierszami okolo 64 px. Uzywamy prawdziwych
    #: liczb, bo wymyslone proporcje przechodza prog w innym miejscu.
    PAGE_WIDTH, PAGE_HEIGHT = 3347, 4800
    STRIP_GUTTER_PX, ROW_GAP_PX = 130, 64

    @classmethod
    def _four_koma(cls):
        """Dwa paski po cztery kadry, w proporcjach zmierzonej strony."""
        gap_x = cls.STRIP_GUTTER_PX / cls.PAGE_WIDTH
        gap_y = cls.ROW_GAP_PX / cls.PAGE_HEIGHT
        column_width = (1.0 - gap_x) / 2
        row_height = (1.0 - 3 * gap_y) / 4
        boxes = []
        for row in range(4):
            top = row * (row_height + gap_y)
            for column, left in enumerate((0.0, column_width + gap_x)):
                boxes.append({
                    "x": left, "y": top, "w": column_width, "h": row_height,
                    "tag": f"{'L' if column == 0 else 'R'}{row + 1}",
                })
        return boxes

    @property
    def aspect(self) -> float:
        return self.PAGE_HEIGHT / self.PAGE_WIDTH

    def test_manga_four_koma_reads_the_right_strip_first(self):
        ordered = order_boxes_by_cuts(self._four_koma(), "rtl", self.aspect)

        assert [box["tag"] for box in ordered] == [
            "R1", "R2", "R3", "R4", "L1", "L2", "L3", "L4",
        ]

    def test_western_four_panel_strip_reads_the_left_strip_first(self):
        ordered = order_boxes_by_cuts(self._four_koma(), "ltr", 4800 / 3347)

        assert [box["tag"] for box in ordered] == [
            "L1", "L2", "L3", "L4", "R1", "R2", "R3", "R4",
        ]

    def test_uniform_gutters_read_in_rows_not_columns(self):
        # Siatka 2x2 z rownymi rynnami w pikselach. Bez poprawki na proporcje
        # strony iloraz wynosilby 1.43 i o wlos decydowalby o zlym wyniku.
        page_aspect = 4800 / 3347
        gutter_px = 60
        gap_x = gutter_px / 3347
        gap_y = gutter_px / 4800
        width = (1.0 - gap_x) / 2
        height = (1.0 - gap_y) / 2
        boxes = [
            {"x": 0.0, "y": 0.0, "w": width, "h": height, "tag": "top-left"},
            {"x": width + gap_x, "y": 0.0, "w": width, "h": height, "tag": "top-right"},
            {"x": 0.0, "y": height + gap_y, "w": width, "h": height, "tag": "bottom-left"},
            {"x": width + gap_x, "y": height + gap_y, "w": width, "h": height, "tag": "bottom-right"},
        ]

        ordered = order_boxes_by_cuts(boxes, "ltr", page_aspect)

        assert [box["tag"] for box in ordered] == [
            "top-left", "top-right", "bottom-left", "bottom-right",
        ]

    def test_uniform_gutters_in_manga_still_read_rows_right_to_left(self):
        page_aspect = 4800 / 3347
        gap_x, gap_y = 60 / 3347, 60 / 4800
        width, height = (1.0 - gap_x) / 2, (1.0 - gap_y) / 2
        boxes = [
            {"x": 0.0, "y": 0.0, "w": width, "h": height, "tag": "top-left"},
            {"x": width + gap_x, "y": 0.0, "w": width, "h": height, "tag": "top-right"},
            {"x": 0.0, "y": height + gap_y, "w": width, "h": height, "tag": "bottom-left"},
            {"x": width + gap_x, "y": height + gap_y, "w": width, "h": height, "tag": "bottom-right"},
        ]

        ordered = order_boxes_by_cuts(boxes, "rtl", page_aspect)

        assert [box["tag"] for box in ordered] == [
            "top-right", "top-left", "bottom-right", "bottom-left",
        ]

    def test_tall_panel_beside_two_stacked_is_read_as_one_column(self):
        # Uklad czesty w mandze: wysoki kadr obok dwoch spietrzonych. Sortowanie
        # pasmami sklejalo go z gornym i gubilo dolny.
        boxes = [
            {"x": 0.0, "y": 0.0, "w": 0.46, "h": 0.98, "tag": "tall"},
            {"x": 0.52, "y": 0.0, "w": 0.46, "h": 0.47, "tag": "upper"},
            {"x": 0.52, "y": 0.52, "w": 0.46, "h": 0.46, "tag": "lower"},
        ]

        ordered = order_boxes_by_cuts(boxes, "rtl", 1.45)

        assert [box["tag"] for box in ordered] == ["upper", "lower", "tall"]

    def test_single_panel_and_empty_input_are_left_alone(self):
        single = [{"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5, "tag": "only"}]

        assert order_boxes_by_cuts(single, "ltr", 1.5) == single
        assert order_boxes_by_cuts([], "ltr", 1.5) == []

    def test_overlapping_panels_fall_back_to_band_sorting(self):
        # Kadry nachodzace na siebie na obu osiach nie daja sie pociac, wiec musi
        # zostac stary porzadek pasmowy zamiast wyjatku.
        boxes = [
            {"x": 0.0, "y": 0.0, "w": 0.7, "h": 0.7, "tag": "a"},
            {"x": 0.3, "y": 0.3, "w": 0.7, "h": 0.7, "tag": "b"},
        ]

        ordered = order_boxes_by_cuts(boxes, "ltr", 1.5)

        assert {box["tag"] for box in ordered} == {"a", "b"}
        assert len(ordered) == 2


class TestPageKind:
    """Rozpoznanie strony poza historia.

    Uklad kadrow jest cecha tytulu, ale rodzaj strony zmienia sie w jego wnetrzu,
    wiec ustawienie per tytul nie oznaczy okladek ani galerii. Liczby pochodza z
    pomiaru na 23 stronach opisanych recznie po ogladzie kazdej z nich.
    """

    def test_cover_and_index_have_no_frames_at_all(self):
        # Vampirella s.024 i s.026 (okladki wariantowe), Azumanga s.680 i s.683
        # (indeks): zero kadrow, zero dymkow.
        assert classify_page_kind(frames=0, balloons=0, coverage=0.0, spread=0.0) == "extra"

    def test_variant_cover_gallery_is_a_grid_of_thumbnails(self):
        # Vampirella s.027: 9 kadrow, pokrycie 34.3%, rozrzut 0.01.
        assert classify_page_kind(frames=9, balloons=0, coverage=0.343, spread=0.01) == "extra"
        # s.028: 7 kadrow, 26.6%, 0.02.
        assert classify_page_kind(frames=7, balloons=0, coverage=0.266, spread=0.02) == "extra"
        # s.029: 10 kadrow, 38.4%, 0.01.
        assert classify_page_kind(frames=10, balloons=0, coverage=0.384, spread=0.01) == "extra"

    def test_publisher_advert_page_is_a_grid_of_thumbnails(self):
        # Vampirella s.022, reklama Dynamite Dispatch: 8 kadrow, 31.2%, 0.02.
        assert classify_page_kind(frames=8, balloons=0, coverage=0.312, spread=0.02) == "extra"

    def test_advert_page_survives_a_more_sensitive_frame_detector(self):
        # Regresja zmierzona przy obnizeniu progu pewnosci kadrow: na tej samej
        # stronie model znalazl dziewiec kadrow o roznych rozmiarach i rozrzut
        # wzrosl z 0.02 na 0.11. Dopoki regula patrzyla na rozrzut, strona
        # przestawala byc dodatkiem i dostawala dziewiec przystankow.
        assert classify_page_kind(frames=9, balloons=0, coverage=0.339, spread=0.11) == "extra"

    def test_uneven_thumbnails_are_still_a_grid(self):
        # Rozrzut nie jest warunkiem, wiec nierowne miniatury tez sa dodatkiem.
        assert classify_page_kind(frames=7, balloons=0, coverage=0.30, spread=0.80) == "extra"

    def test_four_koma_page_without_dialogue_stays_a_story_page(self):
        # Najwazniejszy przypadek. Azumanga s.575 ma zero wykrytych balonow i
        # kadry rowne jak miniatury w galerii (rozrzut 0.01), wiec sam rozrzut by
        # ja odrzucil. Rozdziela je pokrycie: 69.6% wobec 26-38% w galerii.
        assert classify_page_kind(frames=8, balloons=0, coverage=0.696, spread=0.01) == "story"

    def test_any_page_with_dialogue_is_a_story_page(self):
        # Warunek konieczny: strona z dymkiem zawsze nalezy do historii, nawet gdy
        # kadry wygladaja jak siatka.
        assert classify_page_kind(frames=9, balloons=1, coverage=0.30, spread=0.01) == "story"

    def test_silent_action_page_with_varied_panels_stays_a_story_page(self):
        # Vampirella s.009: 2 kadry, 1 dymek, pokrycie 50.1%, rozrzut 0.95.
        assert classify_page_kind(frames=2, balloons=1, coverage=0.501, spread=0.95) == "story"
        # Ta sama strona bez wykrytego dymka nadal ma nierowne kadry.
        assert classify_page_kind(frames=2, balloons=0, coverage=0.501, spread=0.95) == "story"

    def test_measured_story_pages_are_never_flagged_as_extra(self):
        # Pelna lista z pomiaru: (kadry, balony, pokrycie, rozrzut).
        measured = [
            (4, 7, 0.514, 0.27), (2, 1, 0.501, 0.95), (6, 13, 0.873, 0.54),
            (8, 6, 0.641, 0.01), (8, 0, 0.696, 0.01), (8, 9, 0.681, 0.00),
            (8, 10, 0.694, 0.01), (5, 8, 0.882, 0.66), (4, 16, 0.592, 0.30),
            (2, 8, 0.416, 0.10), (5, 7, 0.926, 0.56), (5, 3, 0.960, 0.22),
            (4, 10, 0.739, 0.46), (5, 4, 1.432, 0.52),
        ]

        for frames, balloons, coverage, spread in measured:
            assert classify_page_kind(frames, balloons, coverage, spread) == "story", (
                frames, balloons, coverage, spread,
            )
