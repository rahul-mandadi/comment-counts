"""Build the campaign-vs-organic cluster labelling task.

The spec is blunt about why this exists: "A hand-labelled sample of clusters,
campaign or organic. This is the part that does not compress and does not get
delegated -- without it there is a clustering demo and no result."

The distinction it is after is not technical. Ten thousand people making the
same point in their own words is public opinion. Ten thousand paraphrases of
one supplied paragraph is a mailing list. The pipeline cannot tell those apart
and the difference is the whole claim.

Sampling is stratified by cluster SIZE, and weighted toward the large end,
because a 27,900-member cluster carries 27,900 records of the collapse while a
2-member cluster carries 2. Labelling them at equal rates would spend the
budget where it cannot move the answer.
"""
import json
import random


SIZE_BANDS = [(2, 3), (4, 10), (11, 50), (51, 500), (501, 10 ** 9)]


def stratified_clusters(clusters, per_band=6, seed=17):
    rng = random.Random(seed)
    buckets = {b: [] for b in SIZE_BANDS}
    for c in clusters:
        n = len(c)
        for lo, hi in SIZE_BANDS:
            if lo <= n <= hi:
                buckets[(lo, hi)].append(c)
                break
    out = []
    for band, cs in buckets.items():
        rng.shuffle(cs)
        for c in cs[:per_band]:
            out.append({"band": f"{band[0]}-{band[1] if band[1] < 10**9 else 'max'}",
                        "size": len(c), "members": c})
    return out, {f"{b[0]}-{b[1] if b[1]<10**9 else 'max'}": len(v) for b, v in buckets.items()}


RUBRIC = """\
For each CLUSTER, choose one.

  campaign  The members are one supplied text. An organisation wrote it and
            people sent it. Wording may vary -- campaign tools paraphrase --
            but there is one source document behind them.

  organic   The members each wrote their own, and the pipeline grouped them
            because they happen to make a similar point. Ten thousand people
            independently saying "this rule is too weak" is public opinion,
            not a mailing list.

  mixed     A real campaign with genuinely independent submissions swept in
            alongside it.

  unusable  Cannot tell from the excerpts shown.

If torn between `campaign` and `organic`, choose `organic`. Calling genuine
public opinion a campaign is the error that erases people from the record;
the reverse merely undercounts coordination.
"""


def write_task(sample, texts, ids, path, per_cluster=3, excerpt=600):
    with open(path, "w") as fh:
        fh.write("# " + RUBRIC.replace("\n", "\n# ") + "\n")
        fh.write("# Keys: c=campaign  o=organic  m=mixed  u=unusable\n")
        for k, s in enumerate(sample):
            mem = s["members"][:per_cluster]
            fh.write(json.dumps({
                "cluster": k, "band": s["band"], "size": s["size"], "label": "",
                "member_ids": [ids[i] for i in mem],
                "members": [texts[i][:excerpt] for i in mem],
            }) + "\n")
    return len(sample)
