"""Rung 3: dense embeddings.

Documents here are whole regulatory comments, many of them extracted from
multi-page PDFs, so they are far longer than the encoder's 256-token window.
Truncating to the first window would be a silent bug of a specific kind: mass
campaign letters often carry a personalised opening and an identical body, so
first-window truncation compares exactly the part that was varied on purpose.

So each document is chunked and the chunk vectors are mean-pooled. That makes
the representation about the whole submission rather than its salutation.
"""
import numpy as np

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_WORDS = 180
MAX_CHUNKS = 24          # ~4,300 words; beyond this, more text stops moving the mean


def chunk(text, size=CHUNK_WORDS, max_chunks=MAX_CHUNKS):
    words = text.split()
    if not words:
        return [""]
    out = [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
    return out[:max_chunks]


def embed_documents(texts, model=None, batch_size=256, show=True):
    from sentence_transformers import SentenceTransformer
    model = model or SentenceTransformer(MODEL)
    flat, owner = [], []
    for i, t in enumerate(texts):
        for c in chunk(t):
            flat.append(c)
            owner.append(i)
    vecs = model.encode(flat, batch_size=batch_size, show_progress_bar=show,
                        convert_to_numpy=True, normalize_embeddings=True)
    dim = vecs.shape[1]
    out = np.zeros((len(texts), dim), dtype=np.float32)
    counts = np.zeros(len(texts), dtype=np.int32)
    for v, o in zip(vecs, owner):
        out[o] += v
        counts[o] += 1
    out /= np.maximum(counts, 1)[:, None]
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.maximum(norms, 1e-9)


def neighbour_pairs(vecs, threshold=0.90, block=512):
    """All pairs above threshold, by blocked exact cosine.

    Exact rather than approximate: 3,487 vectors is 12M comparisons, which is
    under a second in numpy. An ANN index here would add a recall parameter
    that then has to be defended, for no speed that matters at this size.
    """
    n = vecs.shape[0]
    pairs = []
    for s in range(0, n, block):
        e = min(s + block, n)
        sims = vecs[s:e] @ vecs.T
        for local, i in enumerate(range(s, e)):
            row = sims[local]
            js = np.nonzero(row >= threshold)[0]
            for j in js:
                if j > i:
                    pairs.append((i, int(j), float(row[j])))
    return pairs
