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
IN = os.path.join(HERE, "labels", "for_human.jsonl")
OUT = os.path.join(HERE, "labels", "human_labels.json")

KEYS = {"s": "same", "v": "variant", "d": "distinct", "u": "unusable"}

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
        pid = str(r["pair"])
        if pid in done:
            i += 1
            continue
        os.system("clear")
        print(f"pair {pid}   ({len(done)}/{len(rows)} labelled)")
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
        if choice not in KEYS:
            continue
        done[pid] = KEYS[choice]
        json.dump(done, open(OUT, "w"), indent=1, sort_keys=True)
        i += 1

    json.dump(done, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"\nsaved {len(done)}/{len(rows)} to {OUT}")
    if len(done) == len(rows):
        print("all done. run:  PYTHONPATH=src .venv/bin/python src/agreement.py")


if __name__ == "__main__":
    sys.exit(main())
