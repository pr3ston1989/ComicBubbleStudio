import copy
import pytest
from tools.bubble_studio.reading_coverage import inspect_page


def fixture():
    reference = dict(
        sha_prefix="abc",
        image_sha256="same",
        name="page",
        direction="ltr",
        complete=True,
        utterances=[dict(label="joined", points=[[0.2, 0.2], [0.7, 0.2]])],
    )

    def region(identity, x):
        return dict(id=identity, x=x, y=0.1, w=0.2, h=0.2, order=int(identity[1:]))

    document = dict(
        lab=dict(sha256="same"),
        result=dict(direction="ltr", bubbles=[region("b1", 0.1), region("b2", 0.6)]),
    )
    return reference, document


def test_split_text_is_present_without_falsely_claiming_one_physical_region():
    reference, document = fixture()
    result = inspect_page(reference, document)
    assert result["covered_points"] == result["reference_points"] == 2
    assert len(result["fragmented_but_all_points_covered"]) == 1
    assert not result["fully_uncovered_stops"] and not result["partly_uncovered_stops"]


def test_a_missing_lobe_remains_a_real_partial_coverage_failure():
    reference, document = fixture()
    document["result"]["bubbles"].pop()
    result = inspect_page(reference, document)
    assert result["covered_points"] == 1
    assert result["partly_uncovered_stops"][0]["missing_point_indices"] == [2]
    assert not result["fragmented_but_all_points_covered"]


def test_duplicate_coverage_and_an_empty_false_region_remain_visible():
    reference, document = fixture()
    duplicate = copy.deepcopy(document["result"]["bubbles"][0])
    duplicate.update(id="b3", order=3)
    empty = dict(id="b4", order=4, x=0.1, y=0.7, w=0.2, h=0.2)
    document["result"]["bubbles"] += [duplicate, empty]
    result = inspect_page(reference, document)
    assert result["covered_points"] == 2
    assert len(result["multiply_covered_points"]) == 1
    assert result["regions_without_reference_point"] == ["b4"]


def test_wrong_image_identity_cannot_produce_a_coverage_percentage():
    reference, document = fixture()
    document["lab"]["sha256"] = "different"
    with pytest.raises(ValueError):
        inspect_page(reference, document)


def test_one_large_mask_covering_two_separate_stops_is_reported_as_shared():
    reference, document = fixture()
    reference["utterances"] = [
        dict(label="first", points=[[0.2, 0.2]]),
        dict(label="second", points=[[0.7, 0.2]]),
    ]
    document["result"]["bubbles"] = [dict(id="b1", order=1, x=0.1, y=0.1, w=0.7, h=0.2)]
    result = inspect_page(reference, document)
    assert result["covered_points"] == 2
    assert result["regions_covering_multiple_stops"] == [
        dict(region_id="b1", utterances=[1, 2])
    ]
