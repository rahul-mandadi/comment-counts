#!/usr/bin/env python3
"""Label the pair sample, one keypress each.

    .venv/bin/python label_pairs.py

Writes labels/human_labels.json as it goes, so it is safe to quit and resume.
Deliberately does NOT show the machine label or the similarity score: the whole
value of these labels is that they are independent of both.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# `python label_pairs.py jaccard` labels the second, Jaccard-stratified sample.
# Kept as separate files rather than one pool because the two samples answer
# different questions and must not be pooled when a threshold is selected: the
# cosine sample constrains the embedding rung, the Jaccard sample the near rung.
SETS = {
    "cosine": ("for_human.jsonl", "human_labels.json"),
    "jaccard": ("for_human_jaccard.jsonl", "human_labels_jaccard.json"),
    "check": ("for_human_jaccard_subset.jsonl", "human_labels_jaccard.json"),
    "clusters": ("for_human_clusters.jsonl", "human_labels_clusters.json"),
    "big": ("for_human_clusters_big.jsonl", "human_labels_clusters.json"),
}
_which = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in SETS else "cosine"
IN = os.path.join(HERE, "labels", SETS[_which][0])
OUT = os.path.join(HERE, "labels", SETS[_which][1])

KEYS = {"s": "same", "v": "variant", "d": "distinct", "u": "unusable"}
CLUSTER_KEYS = {"c": "campaign", "o": "organic", "m": "mixed", "u": "unusable"}

CLUSTER_RUBRIC = """
  [c] campaign  The members are one supplied text. An organisation wrote it and
                people sent it. Wording may vary -- campaign tools paraphrase --
                but there is one source document behind them.
  [o] organic   Each member wrote their own; the pipeline grouped them because
                they make a similar point. Ten thousand people independently
                saying "this rule is too weak" is public opinion.
  [m] mixed     A real campaign with independent submissions swept in alongside.
  [u] unusable  Cannot tell from the excerpts shown.

  Torn between campaign and organic? Choose ORGANIC. Calling genuine public
  opinion a campaign is the error that erases people from the record.

  [q] quit and save   [b] go back one
"""

RUBRIC = """
  [s] same      Same argument; the second adds no substantive point the first
                makes. Different signature, town, or one line of personal
                context still counts as same.
  [v] variant   Clearly from a common source, but one adds a real point of its
                own (new objection, new evidence, different remedy asked for).
  [d] distinct  Independently made arguments, even if they reach the same
                conclusion. Two people saying "this rule is too weak" in their
                own words are DISTINCT. That is public opinion, not a campaign.
  [u] unusable  Too garbled or truncated to judge.

  Torn between same and distinct? Choose DISTINCT. Merging two real arguments
  erases someone from the public record; splitting a campaign only overstates
  diversity.

  [q] quit and save   [b] go back one
"""


def main():
    rows = [json.loads(l) for l in open(IN) if not l.startswith("#")]
    done = json.load(open(OUT)) if os.path.exists(OUT) else {}
    i = 0
    while i < len(rows):
        r = rows[i]
        pid = str(r.get("pair", r.get("cluster")))
        if pid in done:
            i += 1
            continue
        os.system("clear")
        keys = CLUSTER_KEYS if "cluster" in r else KEYS
        if "cluster" in r:
            print(f"[clusters] cluster {pid}   ({len(done)}/{len(rows)} labelled)"
                  f"   SIZE = {r['size']:,} records")
            print("=" * 78)
            for n, m in enumerate(r["members"]):
                print(f"member {n + 1}: {m.strip()[:700]}")
                print("-" * 78)
            print(CLUSTER_RUBRIC)
        else:
            print(f"[{_which}] pair {pid}   ({len(done)}/{len(rows)} labelled)")
            print("=" * 78)
            print("A:", r["a_text"][:1100].strip())
            print("-" * 78)
            print("B:", r["b_text"][:1100].strip())
            print("=" * 78)
            print(RUBRIC)
        choice = input("label > ").strip().lower()
        if choice == "q":
            break
        if choice == "b":
            prev = str(rows[max(0, i - 1)]["pair"])
            done.pop(prev, None)
            i = max(0, i - 1)
            continue
        if choice not in keys:
            continue
        done[pid] = keys[choice]
        json.dump(done, open(OUT, "w"), indent=1, sort_keys=True)
        i += 1

    json.dump(done, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"\nsaved {len(done)}/{len(rows)} to {OUT}")
    if len(done) == len(rows):
        print("all done. run:  PYTHONPATH=src .venv/bin/python src/select.py")


if __name__ == "__main__":
    sys.exit(main())
