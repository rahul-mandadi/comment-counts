"""Phase 2: one docket end to end, at the operating point chosen from labels.

THE THRESHOLDS ARE NOT RE-TUNED PER DOCKET, and that is a deliberate choice with
a cost. They were selected once, on 31 blind human labels drawn from
EPA-HQ-OAR-2021-0317, as the lowest threshold still achieving precision 1.00.
Re-tuning per docket would mean choosing an operating point against the outcome
variable on each docket in turn, which is how a cross-docket comparison stops
being a comparison.

The cost is an untested assumption: that a cosine of 0.964 means the same thing
on an Education docket as on an EPA one. The corpus makes that plausible -- all
six are English-language public comments on federal rules -- but plausible is not
measured, and it is recorded in the report as a bound rather than waved past.
"""
import json
import os
import sys
import time

import numpy as np

import analysis
import clean
import corpus
import dedup
import embed

# selected on human labels, 2026-09-20, at precision 1.00
COSINE = 0.9641
# 80/128 exactly. 0.7891 was the top of a plateau the first label sample could
# not constrain: no labelled pair had a Jaccard between 0.3438 and 0.7891, so
# every threshold in that 0.445-wide window scored precision 1.00 and the
# selection rule returned the end that minimised collapse. A second sample of
# 40 pairs stratified over Jaccard, 11 of them labelled by a human, narrowed
# the admissible window to 0.0156 and put the threshold here.
JACCARD = 80 / 128


def run(docket, store=None, save_vectors=True):
    t0 = time.time()
    all_rows = corpus.load(docket)
    # count the docket, THEN filter. assemble.py promises records with no usable
    # text are "counted and reported, never silently dropped", and computing the
    # totals after the filter broke that promise: EPA-HQ-OAR-2021-0317 reported
    # 38 such records when the real figure is 129, 2.5% of the docket.
    no_text_at_assembly = sum(1 for r in all_rows if r["source"] == "none")
    rows = [r for r in all_rows if r["source"] != "none"]
    texts = [clean.clean(r["text"]) for r in rows]
    keep = [i for i, t in enumerate(texts) if t.strip()]
    kr = [rows[i] for i in keep]
    kt = [texts[i] for i in keep]
    n = len(keep)
    sys.stderr.write(f"{docket}: {len(rows)} records, {n} with usable text\n")

    v = embed.embed_documents(kt, show=False)
    mh = dedup.MinHasher(num_perm=128, seed=17)
    sigs = np.array([mh.signature(dedup.shingles(t)) for t in kt])
    cand = dedup.lsh_candidate_pairs(sigs, bands=32, rows=4)
    near_pairs = [(i, j) for i, j in cand
                  if dedup.jaccard(sigs[i], sigs[j]) >= JACCARD]
    # Complete linkage on BOTH rungs. Phase 1's headline comparison is stated as
    # like-for-like; this file previously clustered near with connected
    # components (single linkage) and semantic with complete, so Phase 2 was not
    # reproducing the comparison it reports. The gap is small here (7.94% vs
    # 7.34% on EPA) but it is unbounded in campaign size, and FWS and ED are
    # exactly the campaign-heavy cases.
    near_clusters = analysis.minhash_complete_clusters(sigs, JACCARD, texts=kt)

    sem, meta = analysis.scalable_clusters(
        v, COSINE, texts=kt,
        progress=lambda d, t: sys.stderr.write(f'  cluster {d}/{t}\r'))
    out = {
        "docket": docket,
        "records_in_docket": len(all_rows),
        "records_usable": n,
        "no_usable_text": len(all_rows) - n,
        "no_text_at_assembly": no_text_at_assembly,
        "emptied_by_cleaning": len(rows) - n,
        "graph": meta,
        "rungs": {
            "exact": analysis.ladder_row("exact", kr, analysis.exact_clusters(kt), n),
            "near": analysis.ladder_row("near", kr, near_clusters, n),
            "near_single_link": analysis.ladder_row(
                "near_single", kr, dedup.components(n, near_pairs), n)["clusters"],
            "semantic": analysis.ladder_row("semantic", kr, sem, n),
        },
        # an oversized component falls back to SINGLE linkage, which is the
        # chaining artifact complete linkage exists to prevent. Never let that
        # sit inside a collapse figure unflagged.
        "semantic_linkage": ("complete" if not meta["oversized_components"]
                             else "MIXED: %d component(s) fell back to single "
                                  "linkage, sizes %s" % (len(meta["oversized_components"]),
                                                         meta["oversized_components"])),
        "margin": analysis.margin_over_official(kr, sem),
        "thresholds": {"cosine": COSINE, "jaccard": JACCARD,
                       "selected_on": "41 blind human labels on EPA-HQ-OAR-2021-0317, pooled from a cosine-stratified and a Jaccard-stratified sample"},
        "seconds": round(time.time() - t0, 1),
    }
    if store is not None:
        store.put_bytes(f"results/{docket}/summary.json",
                        json.dumps(out, indent=1).encode())
        if save_vectors:
            np.save(f"/tmp/{docket}_v.npy", v)
            store.upload_file(f"/tmp/{docket}_v.npy", f"embeddings/{docket}/vectors.npy")
            os.remove(f"/tmp/{docket}_v.npy")
        store.put_bytes(f"corpus/{docket}/clean.jsonl",
                        "\n".join(json.dumps({"id": r["id"], "text": t,
                                              "duplicateComments": r["duplicateComments"]})
                                  for r, t in zip(kr, kt)).encode())
    return out


if __name__ == "__main__":
    import store as store_mod
    s = store_mod.from_env() if os.environ.get("COMMENT_COUNTS_BUCKET") else None
    print(json.dumps(run(sys.argv[1], store=s), indent=1))
