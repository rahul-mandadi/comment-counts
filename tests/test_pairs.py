import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pairs


def test_stratification_spreads_across_bands_not_just_the_easy_end():
    scored = [(0, k, 0.62) for k in range(1, 200)] + [(1, k, 0.995) for k in range(200, 400)]
    sample, counts = pairs.stratified_pairs(scored, per_band=10)
    bands = {p["band"] for p in sample}
    assert "0.60-0.70" in bands and "0.99-1.01" in bands
    assert sum(1 for p in sample if p["band"] == "0.60-0.70") == 10


def test_a_band_with_few_pairs_contributes_all_of_them_not_zero():
    scored = [(0, 1, 0.72), (0, 2, 0.73)] + [(3, k, 0.96) for k in range(10, 60)]
    sample, _ = pairs.stratified_pairs(scored, per_band=20)
    assert sum(1 for p in sample if p["band"] == "0.70-0.80") == 2


def test_sampling_is_deterministic_for_a_seed():
    scored = [(0, k, 0.72 + (k % 5) * 0.001) for k in range(1, 300)]
    a, _ = pairs.stratified_pairs(scored, per_band=7, seed=4)
    b, _ = pairs.stratified_pairs(scored, per_band=7, seed=4)
    assert a == b


def test_rubric_states_the_tie_break_toward_distinct():
    # the asymmetry is declared in advance; losing it would silently change the
    # operating point the whole result rests on
    assert "choose `distinct`" in pairs.RUBRIC
