"""Precision and recall per rung, against the labelled pair sample.

A caveat that belongs next to every number this produces, not in an appendix:
the sample is stratified over SEMANTIC similarity bands. So these figures
describe behaviour on pairs drawn by that design, and they are not population
estimates. In particular the exact and near rungs are being judged on a sample
selected by a different rung's ranking, which over-represents the region where
they fire. Use these to choose an operating point; do not quote them as "the
precision of MinHash on federal dockets".
"""


def merges(rung, i, j, sigs=None, vecs=None, keys=None, threshold=None):
    if rung == "exact":
        return keys[i] == keys[j]
    if rung == "near":
        import numpy as np
        return float(np.mean(sigs[i] == sigs[j])) >= threshold
    if rung == "semantic":
        return float(vecs[i] @ vecs[j]) >= threshold
    raise ValueError(rung)


def score(labels, predicted_merge, positive=("same",), ignore=("unusable",)):
    tp = fp = fn = tn = 0
    for pair, lab in labels.items():
        if lab in ignore or pair not in predicted_merge:
            continue
        pos = lab in positive
        pred = predicted_merge[pair]
        if pred and pos:
            tp += 1
        elif pred and not pos:
            fp += 1
        elif not pred and pos:
            fn += 1
        else:
            tn += 1
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = (2 * prec * rec / (prec + rec)) if prec and rec else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(prec, 4) if prec is not None else None,
            "recall": round(rec, 4) if rec is not None else None,
            "f1": round(f1, 4) if f1 else None}
