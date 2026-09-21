"""Derive the operating point from the labels. THE headline must be re-runnable.

NAMED `threshold_select`, not `select`. `src/` is on PYTHONPATH, so a module
called `select.py` shadows the standard library's `select`, and everything that
reaches it -- subprocess, asyncio, torch's loaders -- dies with
`AttributeError: module 'select' has no attribute 'select'`. That took out a
Phase 2 run within minutes of the file being added.

`docs/phase1.md` has stated the ladder comparison wrongly twice, and both times
the numbers lived only in a chat transcript and a markdown table. Nothing in the
repo recomputed them, so nothing could contradict them. This does.

It also reports what the earlier versions could not: **how much the labels
actually constrain each threshold.** A threshold is only meaningful if moving it
within the label-admissible range changes the answer little. On this label set
that is true of cosine and spectacularly false of Jaccard.

    PYTHONPATH=src .venv/bin/python src/threshold_select.py
"""
import json
import os
import sys

import numpy as np

import bedrock_embed as be
import clean
import corpus
import dedup

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKET = "EPA-HQ-OAR-2021-0317"


def load_labelled():
    labs = json.load(open(os.path.join(HERE, "labels", "human_labels.json")))
    sample = json.load(open(os.path.join(HERE, "out", "pairs_sample.json")))
    rows = [r for r in corpus.load(DOCKET) if r["source"] != "none"]
    texts = [clean.clean(r["text"]) for r in rows]
    v = np.load(os.path.join(HERE, "data", DOCKET, "vecs_v3.npy"))
    mh = dedup.MinHasher(num_perm=128, seed=17)
    cache = {}

    def sig(i):
        if i not in cache:
            cache[i] = mh.signature(dedup.shingles(texts[i]))
        return cache[i]

    out = []
    for p, lab in labs.items():
        if lab == "unusable":
            continue
        s = sample[int(p)]
        out.append({
            "pair": int(p), "label": lab, "positive": lab == "same",
            "cosine": float(v[s["i"]] @ v[s["j"]]),
            "jaccard": float(np.mean(sig(s["i"]) == sig(s["j"]))),
        })
    return out


def admissible_range(rows, key, min_precision=1.0):
    """(low, high] of thresholds that all achieve min_precision on these labels.

    `high` is what select_threshold returns. `low` is the top negative, i.e. the
    point below which precision breaks. Everything in between is indistinguishable
    ON THIS LABEL SET, so the width is a direct measure of how much the labels
    are actually deciding.
    """
    pos = sorted(r[key] for r in rows if r["positive"])
    neg = sorted(r[key] for r in rows if not r["positive"])
    top_neg = neg[-1] if neg else 0.0
    high = be.select_threshold([r[key] for r in rows],
                               [r["positive"] for r in rows], min_precision)
    n_between = sum(1 for p in pos if top_neg < p <= (high or 0))
    return {"top_negative": round(top_neg, 4),
            "selected": None if high is None else round(high, 4),
            "width": None if high is None else round(high - top_neg, 4),
            "positives_in_range": n_between}


def main():
    rows = load_labelled()
    out = {"docket": DOCKET, "labels_used": len(rows),
           "positives": sum(1 for r in rows if r["positive"])}
    for key in ("cosine", "jaccard"):
        out[key] = admissible_range(rows, key)
    print(json.dumps(out, indent=1))

    print("\nHOW MUCH DO THE LABELS CONSTRAIN EACH RUNG?", file=sys.stderr)
    for key in ("cosine", "jaccard"):
        a = out[key]
        print(f"  {key:8} admissible ({a['top_negative']}, {a['selected']}]  "
              f"width {a['width']}", file=sys.stderr)
    return out


if __name__ == "__main__":
    main()
