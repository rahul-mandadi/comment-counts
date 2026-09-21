import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import dedup


def test_exact_ignores_case_and_whitespace_only():
    assert dedup.exact_key("The  RULE\nis good") == dedup.exact_key("the rule is good")


def test_exact_does_NOT_merge_a_form_letter_signed_by_two_people():
    # if it did, rung 1 and rung 2 would measure the same thing
    a = "I oppose this rule. Sincerely, Jane Smith"
    b = "I oppose this rule. Sincerely, John Doe"
    assert dedup.exact_key(a) != dedup.exact_key(b)


def test_near_DOES_merge_that_pair():
    mh = dedup.MinHasher(num_perm=128)
    a = "I oppose this rule because methane leaks harm my community. Sincerely, Jane Smith"
    b = "I oppose this rule because methane leaks harm my community. Sincerely, John Doe"
    assert dedup.jaccard(mh.signature(dedup.shingles(a)),
                         mh.signature(dedup.shingles(b))) > 0.5


def test_near_does_not_merge_two_unrelated_comments():
    mh = dedup.MinHasher(num_perm=128)
    a = "I oppose this rule because methane leaks harm my community in Colorado."
    b = "Our association supports flexible compliance timelines for marginal wells."
    assert dedup.jaccard(mh.signature(dedup.shingles(a)),
                         mh.signature(dedup.shingles(b))) < 0.3


def test_minhash_estimates_jaccard_within_tolerance():
    mh = dedup.MinHasher(num_perm=256, seed=3)
    A = {f"s{i}" for i in range(100)}
    B = {f"s{i}" for i in range(50, 150)}
    true = len(A & B) / len(A | B)          # 50/150
    est = dedup.jaccard(mh.signature(A), mh.signature(B))
    assert abs(est - true) < 0.08, (est, true)


def test_identical_sets_have_identical_signatures():
    mh = dedup.MinHasher(num_perm=64)
    s = {"a b c d e", "b c d e f"}
    assert np.array_equal(mh.signature(s), mh.signature(set(s)))


def test_shingles_of_a_short_text_do_not_vanish():
    assert dedup.shingles("No.", k=5) == {"no"}


def test_components_are_transitive():
    assert sorted(len(g) for g in dedup.components(4, [(0, 1), (1, 2)])) == [1, 3]


def test_lsh_finds_a_planted_near_duplicate():
    mh = dedup.MinHasher(num_perm=128, seed=5)
    base = " ".join(f"word{i}" for i in range(200))
    texts = [base, base + " signed by jane smith",
             " ".join(f"other{i}" for i in range(200))]
    sigs = np.array([mh.signature(dedup.shingles(t)) for t in texts])
    pairs = dedup.lsh_candidate_pairs(sigs, bands=32, rows=4)
    assert (0, 1) in pairs and (0, 2) not in pairs and (1, 2) not in pairs


def test_complete_linkage_refuses_to_chain():
    """The defect this exists to fix, in three points.

    A-B are close, B-C are close, A-C are not. Single linkage (connected
    components) makes one cluster of three. Complete linkage must not.
    """
    import numpy as np, analysis, dedup, math
    ang = [0.0, 0.34, 0.68]          # radians apart; A-C is twice A-B
    v = np.array([[math.cos(a), math.sin(a)] for a in ang], dtype=np.float32)
    thr = float(v[0] @ v[1]) - 1e-6  # threshold that admits A-B and B-C only
    assert v[0] @ v[2] < thr < v[0] @ v[1]

    single = dedup.components(3, [(0, 1), (1, 2)])
    assert sorted(len(c) for c in single) == [3]

    complete = analysis.complete_link_clusters(v, thr)
    assert sorted(len(c) for c in complete) == [1, 2], complete


def test_scalable_clustering_matches_the_dense_version():
    """The memory optimisation must not change the answer."""
    import numpy as np, analysis
    rng = np.random.default_rng(11)
    # three tight groups plus noise, so there is real structure to preserve
    centres = rng.normal(size=(3, 12))
    v = np.vstack([c + 0.02 * rng.normal(size=(15, 12)) for c in centres]
                  + [rng.normal(size=(10, 12))]).astype(np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    thr = 0.95
    dense = analysis.complete_link_clusters(v, thr)
    sparse, meta = analysis.scalable_clusters(v, thr, max_component=1000)
    norm = lambda cs: sorted(sorted(c) for c in cs)
    assert norm(dense) == norm(sparse), (len(dense), len(sparse))
    assert meta["oversized_components"] == []


def test_scalable_clustering_reports_an_oversized_component_instead_of_approximating():
    import numpy as np, analysis
    v = np.ones((30, 4), dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)   # all identical -> one component
    _cl, meta = analysis.scalable_clusters(v, 0.9, max_component=10)
    assert meta["oversized_components"] == [30]


def test_clustering_survives_a_mass_campaign_without_materialising_pairs():
    """The defect that killed a run: 27,807 identical docs on FWS would have
    emitted 386 million pairs. Memory must stay flat in the campaign size."""
    import numpy as np, analysis
    rng = np.random.default_rng(3)
    big = np.tile(np.array([[1.0, 0.0, 0.0]], dtype=np.float32), (800, 1))
    other = np.array([[0.0, 1.0, 0.0]] * 5, dtype=np.float32)
    v = np.vstack([big, other])
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    texts = ["identical campaign letter"] * 800 + [f"unique {i}" for i in range(5)]
    cl, meta = analysis.scalable_clusters(v, 0.95, max_component=50, texts=texts)
    sizes = sorted(len(c) for c in cl)
    assert sizes[-1] == 800, sizes          # the campaign stays one cluster
    assert meta["oversized_components"] == []   # collapsed by hash, not abandoned
    assert sum(len(c) for c in cl) == 805       # nothing lost


def test_identical_docs_are_never_split_by_the_representative_step():
    import numpy as np, analysis
    v = np.ones((300, 3), dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    texts = ["same"] * 300
    cl, _ = analysis.scalable_clusters(v, 0.99, max_component=10, texts=texts)
    assert len(cl) == 1 and len(cl[0]) == 300
