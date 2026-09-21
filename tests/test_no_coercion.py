import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import analysis


def test_an_unpopulated_field_is_not_reported_as_one_submission_each():
    """`or 1` rewrote 0 to 1 and manufactured an agency-behaviour finding.
    ED and OSHA carry 0 on every record; that is 'unknown', not 'one each'."""
    rows = [{"duplicateComments": 0} for _ in range(100)]
    s = analysis.submissions(rows)
    assert s["total"] is None and s["field_populated"] is False
    m = analysis.margin_over_official(rows, [[i] for i in range(100)])
    assert m["official_collapse"] is None and m["submissions"] is None


def test_a_populated_field_still_sums():
    rows = [{"duplicateComments": 1}] * 9 + [{"duplicateComments": 500}]
    s = analysis.submissions(rows)
    assert s["total"] == 509 and s["field_populated"] is True


def test_a_docket_with_one_populated_record_counts_as_populated():
    # FWS has 14 such records in 64,019. It IS using the field.
    rows = [{"duplicateComments": 1}] * 50 + [{"duplicateComments": 89}]
    assert analysis.submissions(rows)["field_populated"] is True
