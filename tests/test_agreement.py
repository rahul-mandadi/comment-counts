import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import agreement


def test_perfect_agreement_is_kappa_one():
    a = ["same", "distinct", "same", "variant"]
    assert agreement.cohens_kappa(a, list(a)) == 1.0


def test_chance_agreement_scores_near_zero_not_near_half():
    # the point of kappa on a ~50/50 sample: a coin flip must not look good
    a = ["same", "distinct"] * 20
    b = ["same", "same", "distinct", "distinct"] * 10
    assert abs(agreement.cohens_kappa(a, b)) < 0.2


def test_systematic_disagreement_is_negative():
    a = ["same"] * 10 + ["distinct"] * 10
    b = ["distinct"] * 10 + ["same"] * 10
    assert agreement.cohens_kappa(a, b) < 0


def test_empty_input_does_not_crash():
    assert agreement.cohens_kappa([], []) is None


def test_bootstrap_ci_brackets_the_point_estimate():
    a = ["same"] * 30 + ["distinct"] * 20
    b = ["same"] * 27 + ["distinct"] * 3 + ["distinct"] * 18 + ["same"] * 2
    k = agreement.cohens_kappa(a, b)
    lo, hi = agreement.bootstrap_kappa_ci(a, b, n=400)
    assert lo <= k <= hi


def test_bootstrap_ci_declines_on_a_tiny_sample():
    assert agreement.bootstrap_kappa_ci(["same"], ["same"]) is None
