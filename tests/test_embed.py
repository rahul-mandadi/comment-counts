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


def test_batched_embedding_equals_unbatched():
    """The memory fix must not change a single vector."""
    import numpy as np
    class FakeModel:
        def encode(self, texts, **kw):
            # deterministic per-string vector, so batching is the only variable
            v = np.array([[float(sum(map(ord, t)) % 97), float(len(t) % 13), 1.0]
                          for t in texts], dtype=np.float32)
            return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    texts = [" ".join(f"w{i}{j}" for j in range(400)) for i in range(25)]
    a = embed.embed_documents(texts, model=FakeModel(), show=False, doc_batch=1000)
    b = embed.embed_documents(texts, model=FakeModel(), show=False, doc_batch=3)
    assert np.allclose(a, b, atol=1e-6)


def test_batching_handles_a_corpus_smaller_than_one_batch():
    import numpy as np
    class FakeModel:
        def encode(self, texts, **kw):
            v = np.ones((len(texts), 4), dtype=np.float32)
            return v / np.linalg.norm(v, axis=1, keepdims=True)
    out = embed.embed_documents(["a", "b"], model=FakeModel(), show=False, doc_batch=500)
    assert out.shape == (2, 4)
