"""Build the hand-labelling set: comment PAIRS stratified over similarity.

The spec is specific about this and it is right: labels concentrated on obvious
cases measure nothing. A pair at cosine 0.99 is trivially a duplicate and a pair
at 0.20 is trivially not; neither tells you where to put the threshold. So the
sample is stratified across bands, with the bands near the candidate operating
point deliberately over-sampled.

The declared asymmetry, restated here because it decides the labelling rubric:
merging two genuinely distinct arguments ERASES a member of the public from the
record; splitting one campaign into two merely overstates diversity. The first
is worse. So when a labeller is unsure, the label is "distinct".
"""
import json
import random

BANDS = [(0.60, 0.70), (0.70, 0.80), (0.80, 0.85), (0.85, 0.90),
         (0.90, 0.95), (0.95, 0.99), (0.99, 1.01)]

RUBRIC = """\
For each pair, choose ONE label.

  same      The two submissions make the SAME argument, and the second adds no
            substantive point the first does not already make. Wording may
            differ freely. A form letter with a different signature, a different
            town, or one inserted sentence of personal context is `same`.

  variant   Clearly derived from a common source, but one of them adds a real
            substantive point of its own (a new objection, a new piece of
            evidence, a different requested remedy).

  distinct  Two independently made arguments, even if they reach the same
            conclusion. Two people who both say "this rule is too weak" in their
            own words are DISTINCT: that is public opinion, not a campaign.

  unusable  One or both texts are too garbled, truncated or empty to judge.

If you are torn between `same` and `distinct`, choose `distinct`. Merging two
real arguments erases someone from the public record; splitting a campaign only
overstates diversity.
"""


def stratified_pairs(scored_pairs, per_band=20, seed=11):
    """scored_pairs: iterable of (i, j, score). Returns a flat sample list."""
    rng = random.Random(seed)
    buckets = {b: [] for b in BANDS}
    for i, j, s in scored_pairs:
        for lo, hi in BANDS:
            if lo <= s < hi:
                buckets[(lo, hi)].append((i, j, s))
                break
    out = []
    for band, items in buckets.items():
        rng.shuffle(items)
        for i, j, s in items[:per_band]:
            out.append({"i": int(i), "j": int(j), "score": round(float(s), 4),
                        "band": f"{band[0]:.2f}-{band[1]:.2f}"})
    return out, {f"{b[0]:.2f}-{b[1]:.2f}": len(v) for b, v in buckets.items()}


def write_labelling_file(sample, rows, path, excerpt=1200):
    with open(path, "w") as fh:
        fh.write("# " + RUBRIC.replace("\n", "\n# ") + "\n")
        for k, p in enumerate(sample):
            a, b = rows[p["i"]], rows[p["j"]]
            fh.write(json.dumps({
                "pair": k,
                "band": p["band"],
                "score": p["score"],
                "label": "",
                "a_id": a["id"], "b_id": b["id"],
                "a_source": a["source"], "b_source": b["source"],
                "a_dupes": a["duplicateComments"], "b_dupes": b["duplicateComments"],
                "a_text": a["text"][:excerpt],
                "b_text": b["text"][:excerpt],
            }) + "\n")
    return len(sample)
