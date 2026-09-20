"""The three-rung duplicate ladder.

    exact     normalised hash            byte-identical form letters
    near      MinHash + LSH over shingles  light edits, name insertion
    semantic  embeddings + ANN            paraphrase, reordering, summary

Each rung is cheaper than the next, so the question the ladder answers is what
the expensive one buys. A pre-registered kill condition says that if semantic
collapses by roughly the same fraction as exact, embeddings bought nothing and
that IS the finding.

MinHash is implemented here rather than imported. It is forty lines, the
permutation scheme is the thing an interviewer asks about, and a library call
would leave nothing to defend.

Clustering is connected components over the similarity graph at every rung, so
the three are directly comparable. That has a known property worth stating
rather than hiding: components chain, so A~B and B~C puts A with C even if A
and C are not similar. `analysis.py` reports component diameter for this reason.
"""
import hashlib
import re
import unicodedata

import numpy as np

_WORD = re.compile(r"[a-z0-9']+")
_MERSENNE = (1 << 61) - 1


# --------------------------------------------------------------------------
# rung 1: exact
# --------------------------------------------------------------------------
def canonical(text):
    """Case and whitespace only.

    Deliberately does NOT strip names, addresses or punctuation. A form letter
    signed by two different people is two different submissions at this rung,
    and catching that pair is the NEAR rung's job. Normalising it away here
    would make rungs 1 and 2 measure the same thing and the ladder would have
    nothing to compare.
    """
    text = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"\s+", " ", text).strip()


# Measured on OSHA-2010-0034: one industry form letter appears 524 times, and
# the exact rung splits it into groups of 500 and 24 because one batch has its
# curly quotes and en-dashes mangled into `?` by the extraction. The two are
# 99.47% identical and differ in nothing but those characters. Exact hashing is
# SUPPOSED to be brittle, so this is not a bug to fix there -- it is why the
# ladder has a second rung, and the near rung merges them correctly.


def exact_key(text):
    return hashlib.sha256(canonical(text).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# rung 2: near, MinHash + LSH
# --------------------------------------------------------------------------
def shingles(text, k=5):
    """Word k-grams. Word-level rather than character-level because the target
    is inserted names and light edits, which move words, not characters."""
    words = _WORD.findall(canonical(text))
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def _hash64(s):
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")


class MinHasher:
    def __init__(self, num_perm=128, seed=17):
        rng = np.random.default_rng(seed)
        self.a = rng.integers(1, _MERSENNE, size=num_perm, dtype=np.uint64)
        self.b = rng.integers(0, _MERSENNE, size=num_perm, dtype=np.uint64)
        self.num_perm = num_perm

    def signature(self, shingle_set):
        if not shingle_set:
            return np.full(self.num_perm, np.iinfo(np.uint64).max, dtype=np.uint64)
        h = np.array([_hash64(s) % _MERSENNE for s in shingle_set], dtype=np.uint64)
        # (a*h + b) mod Mersenne-61, one column per permutation
        prod = (h[:, None] * self.a[None, :]) % _MERSENNE
        perm = (prod + self.b[None, :]) % _MERSENNE
        return perm.min(axis=0)


def lsh_candidate_pairs(signatures, bands=32, rows=4):
    """Band the signature matrix; any two rows sharing a band are candidates."""
    n, num_perm = signatures.shape
    assert bands * rows <= num_perm, "bands*rows must fit the signature"
    pairs = set()
    for band in range(bands):
        chunk = signatures[:, band * rows:(band + 1) * rows]
        buckets = {}
        for i in range(n):
            key = chunk[i].tobytes()
            buckets.setdefault(key, []).append(i)
        for members in buckets.values():
            if len(members) < 2:
                continue
            # a bucket of size m contributes m(m-1)/2 pairs; cap the blow-up
            # from one enormous form-letter bucket by linking to its first
            # member, which is sufficient for connected components
            if len(members) > 200:
                first = members[0]
                pairs.update((min(first, j), max(first, j)) for j in members[1:])
            else:
                for x in range(len(members)):
                    for y in range(x + 1, len(members)):
                        pairs.add((members[x], members[y]))
    return pairs


def jaccard(sig_a, sig_b):
    return float(np.mean(sig_a == sig_b))


# --------------------------------------------------------------------------
# clustering
# --------------------------------------------------------------------------
class Union:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.p[max(rx, ry)] = min(rx, ry)

    def groups(self):
        out = {}
        for i in range(len(self.p)):
            out.setdefault(self.find(i), []).append(i)
        return list(out.values())


def components(n, pairs):
    u = Union(n)
    for i, j in pairs:
        u.union(i, j)
    return u.groups()
