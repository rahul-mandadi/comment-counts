import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pytest
import bedrock_embed as be


def test_input_carries_a_record_id_per_line():
    raw = be.build_input_jsonl(["a", "b"], ["x", "y"])
    rows = [json.loads(l) for l in raw.strip().splitlines()]
    assert [r["recordId"] for r in rows] == ["a", "b"]
    assert rows[0]["modelInput"]["inputText"] == "x"


def test_output_is_matched_by_id_not_by_position():
    # Bedrock does not guarantee output order; relying on it corrupts silently
    raw = "\n".join([
        json.dumps({"recordId": "b", "modelOutput": {"embedding": [2.0]}}),
        json.dumps({"recordId": "a", "modelOutput": {"embedding": [1.0]}}),
    ])
    got = be.parse_output_jsonl(raw, expected_ids=["a", "b"])
    assert got["a"] == [1.0] and got["b"] == [2.0]


def test_a_dropped_record_raises_instead_of_becoming_a_zero_vector():
    raw = json.dumps({"recordId": "a", "modelOutput": {"embedding": [1.0]}})
    with pytest.raises(ValueError, match="no embedding"):
        be.parse_output_jsonl(raw, expected_ids=["a", "b"])


def test_threshold_selection_respects_the_precision_floor():
    scores = [0.99, 0.98, 0.95, 0.94, 0.80]
    labels = [True, True, True, False, False]
    t = be.select_threshold(scores, labels, min_precision=1.0)
    assert t == 0.95        # admits the three positives, excludes the 0.94 negative


def test_threshold_selection_keeps_the_most_recall_among_qualifying():
    scores = [0.99, 0.97, 0.90]
    labels = [True, True, False]
    assert be.select_threshold(scores, labels, min_precision=1.0) == 0.97


def test_threshold_selection_returns_none_when_nothing_meets_the_bar():
    assert be.select_threshold([0.9, 0.8], [False, False], min_precision=1.0) is None
