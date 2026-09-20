"""Judge-human agreement, and what it does to the reported precision.

The spec's rule: a judge that has not been measured is an unreliable narrator,
and agreement gets reported ALONGSIDE the finding rather than in an appendix.
This computes raw agreement and Cohen's kappa, and then re-derives precision
and recall on the human labels alone so the report can quote a human-grounded
number instead of a machine-grounded one.

Kappa matters more than raw agreement here because the classes are unbalanced:
on the labelled sample roughly half the pairs are `same`, so a coin flip scores
~50% raw agreement and kappa near 0.
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cohens_kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return None
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    expected = sum((ca[l] / n) * (cb[l] / n) for l in labels)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def load():
    m = json.load(open(os.path.join(HERE, "labels", "machine_labels.json")))["labels"]
    hp = os.path.join(HERE, "labels", "human_labels.json")
    if not os.path.exists(hp):
        raise SystemExit("no human labels yet. run:  .venv/bin/python label_pairs.py")
    return m, json.load(open(hp))


def report():
    machine, human = load()
    shared = sorted(set(machine) & set(human), key=int)
    mv = [machine[p] for p in shared]
    hv = [human[p] for p in shared]
    raw = sum(1 for x, y in zip(mv, hv) if x == y) / len(shared) if shared else 0.0

    # binary view: the decision the pipeline actually makes is merge / do not
    mb = ["merge" if x == "same" else "keep" for x in mv]
    hb = ["merge" if x == "same" else "keep" for x in hv]
    raw_b = sum(1 for x, y in zip(mb, hb) if x == y) / len(shared) if shared else 0.0

    disagreements = [{"pair": p, "machine": machine[p], "human": human[p]}
                     for p in shared if machine[p] != human[p]]

    return {
        "pairs_compared": len(shared),
        "raw_agreement_4class": round(raw, 4),
        "kappa_4class": round(cohens_kappa(mv, hv), 4) if shared else None,
        "raw_agreement_merge_vs_keep": round(raw_b, 4),
        "kappa_merge_vs_keep": round(cohens_kappa(mb, hb), 4) if shared else None,
        "machine_distribution": dict(collections.Counter(mv)),
        "human_distribution": dict(collections.Counter(hv)),
        "disagreements": disagreements,
    }


if __name__ == "__main__":
    r = report()
    print(json.dumps(r, indent=1))
    k = r["kappa_merge_vs_keep"]
    if k is None:
        pass
    elif k < 0.6:
        print("\nKAPPA BELOW 0.6. Per the spec's kill condition 4, the judge arm is not "
              "trustworthy enough to carry a finding. Report the dedup result on HUMAN "
              "labels only, and say the machine labels were discarded.")
    else:
        print(f"\nkappa {k}: report it next to the precision table, not in an appendix.")
