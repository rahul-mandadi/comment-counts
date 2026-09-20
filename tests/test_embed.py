import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import embed


def test_chunking_covers_the_whole_document_not_just_the_first_window():
    text = " ".join(f"w{i}" for i in range(1000))
    cs = embed.chunk(text, size=180)
    assert len(cs) == 6
    assert cs[0].startswith("w0 ") and cs[-1].endswith("w999")


def test_chunking_is_capped_so_one_huge_pdf_cannot_dominate():
    text = " ".join(f"w{i}" for i in range(100000))
    assert len(embed.chunk(text, size=180, max_chunks=24)) == 24


def test_empty_text_still_yields_one_chunk():
    assert embed.chunk("") == [""]


def test_neighbour_pairs_respects_threshold_and_is_upper_triangular():
    v = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    pairs = embed.neighbour_pairs(v, threshold=0.9)
    assert [(i, j) for i, j, _s in pairs] == [(0, 1)]


def test_neighbour_pairs_blocking_does_not_change_the_answer():
    rng = np.random.default_rng(0)
    v = rng.normal(size=(60, 8)).astype(np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    a = {(i, j) for i, j, _ in embed.neighbour_pairs(v, 0.5, block=7)}
    b = {(i, j) for i, j, _ in embed.neighbour_pairs(v, 0.5, block=1000)}
    assert a == b
