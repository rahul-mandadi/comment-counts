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
JACCARD = 0.7891


def run(docket, store=None, save_vectors=True):
    t0 = time.time()
    rows = [r for r in corpus.load(docket) if r["source"] != "none"]
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

    sem, meta = analysis.scalable_clusters(
        v, COSINE, texts=kt,
        progress=lambda d, t: sys.stderr.write(f'  cluster {d}/{t}\r'))
    out = {
        "docket": docket,
        "records_total": len(rows),
        "records_usable": n,
        "no_usable_text": len(rows) - n,
        "graph": meta,
        "rungs": {
            "exact": analysis.ladder_row("exact", kr, analysis.exact_clusters(kt), n),
            "near": analysis.ladder_row("near", kr, dedup.components(n, near_pairs), n),
            "semantic": analysis.ladder_row("semantic", kr, sem, n),
        },
        "margin": analysis.margin_over_official(kr, sem),
        "thresholds": {"cosine": COSINE, "jaccard": JACCARD,
                       "selected_on": "31 blind human labels, EPA-HQ-OAR-2021-0317"},
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
