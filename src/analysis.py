"""Collapse ratios, and the margin over the count the government already publishes.

The unit matters more than anything else in this file. A docket has THREE
counts, not two:

    submissions  how many people pressed send      (sum of duplicateComments)
    records      how many entries the docket holds  (what you see on the site)
    clusters     how many distinct things were said (what a rung produces)

regulations.gov already performs the submissions -> records collapse. So a rung
that reports a huge absolute collapse has not necessarily found anything: the
only number that is this project's own contribution is the records -> clusters
step, and it must be reported next to the official one rather than instead of it.
"""
import collections

import dedup


def submissions(rows):
    """Sum of duplicateComments, and whether the field is populated at all.

    Returns None for `total` when no record on the docket carries a value,
    because "unpopulated" and "one submission each" are different facts and
    collapsing them fabricates the second. ED-2021-OCR-0166 and
    OSHA-2010-0034 are wholly unpopulated.
    """
    vals = [r.get("duplicateComments") for r in rows]
    pop = [v for v in vals if v is not None and v > 0]
    if not pop:
        return {"total": None, "populated_records": 0, "records": len(rows),
                "field_populated": False}
    total = sum(v if (v is not None and v > 0) else 1 for v in vals)
    return {"total": total, "populated_records": sum(1 for v in pop if v > 1),
            "records": len(rows), "field_populated": True}


def cluster_stats(rows, clusters):
    """clusters: list of lists of row indices."""
    sizes = [len(c) for c in clusters]
    subs = [sum(rows[i]["duplicateComments"] for i in c) for c in clusters]
    return {
        "clusters": len(clusters),
        "largest_cluster_records": max(sizes) if sizes else 0,
        "largest_cluster_submissions": max(subs) if subs else 0,
        "singletons": sum(1 for s in sizes if s == 1),
        "multi_record_clusters": sum(1 for s in sizes if s > 1),
    }


def ladder_row(name, rows, clusters, baseline_records):
    st = cluster_stats(rows, clusters)
    st["rung"] = name
    st["records_in"] = baseline_records
    st["collapse_vs_records"] = round(baseline_records / max(1, st["clusters"]), 4)
    st["extra_collapse_pct"] = round(
        100 * (1 - st["clusters"] / max(1, baseline_records)), 2)
    return st


def margin_over_official(rows, clusters):
    """What the project adds beyond regulations.gov's own duplicate count."""
    sub = submissions(rows)
    records = len(rows)
    n = len(clusters)
    if sub["total"] is None:
        # The field is unpopulated on this docket, so there IS no published
        # submission count and no official collapse to report. Returning 1.00x
        # here -- which an `or 1` coercion used to do -- invents a government
        # figure and was the basis of a retracted finding.
        return {"submissions": None, "records": records, "clusters": n,
                "official_collapse": None, "field_populated": False,
                "our_additional_collapse": round(records / max(1, n), 4),
                "total_collapse": None,
                "share_of_collapse_already_official": None}
    total = sub["total"]
    return {
        "submissions": total,
        "records": records,
        "clusters": n,
        "field_populated": True,
        "records_with_bundled_counts": sub["populated_records"],
        "official_collapse": round(total / max(1, records), 2),
        "our_additional_collapse": round(records / max(1, n), 4),
        "total_collapse": round(total / max(1, n), 2),
        "share_of_collapse_already_official": round(
            1 - (records / max(1, n) - 1) / max(1e-9, (total / max(1, n) - 1)), 6),
    }


def chain_diameter(clusters, pairs, cap=40):
    """Longest shortest-path inside each component, for the biggest ones.

    Connected components chain: A~B and B~C groups A with C even when A and C
    are not similar. A component with a large diameter is a chain, not a
    campaign, and reporting it as one cluster would overstate the collapse.
    """
    adj = collections.defaultdict(set)
    for i, j in pairs:
        adj[i].add(j)
        adj[j].add(i)
    out = []
    for c in sorted(clusters, key=len, reverse=True)[:cap]:
        if len(c) < 3:
            continue
        member = set(c)
        best = 0
        for src in list(c)[:64]:          # sample sources on big components
            seen = {src: 0}
            q = collections.deque([src])
            while q:
                x = q.popleft()
                for y in adj[x]:
                    if y in member and y not in seen:
                        seen[y] = seen[x] + 1
                        q.append(y)
            best = max(best, max(seen.values()))
        out.append({"size": len(c), "diameter": best})
    return out


def exact_clusters(texts):
    g = collections.defaultdict(list)
    for i, t in enumerate(texts):
        g[dedup.exact_key(t)].append(i)
    return list(g.values())


def complete_link_clusters(vecs, threshold, index_subset=None):
    """Agglomerative clustering with COMPLETE linkage on cosine distance.

    Why this exists, and it is the most important choice in the pipeline.

    Connected components over a similarity graph is SINGLE linkage: one edge is
    enough to merge. On the semantic rung that chains. Measured on
    EPA-HQ-OAR-2021-0317 at cosine 0.90, the largest component holds 849 records
    and has **diameter 14** -- a path of fourteen hops, so the documents at its
    ends are not similar to each other at all. At 0.85 it swallows 1,744 records
    and 655,495 submissions, which is 78% of the docket, and reporting that as
    one campaign would have been a fabricated finding.

    Complete linkage requires EVERY pair in a cluster to sit above the
    threshold, so a chain cannot form. That is also the conservative direction
    for the asymmetry this project declared in advance: merging two genuinely
    distinct arguments erases a member of the public from the record, and
    splitting one campaign in two merely overstates diversity. The first is
    worse, so the operating point favours precision.
    """
    import numpy as np
    from sklearn.cluster import AgglomerativeClustering

    idx = list(range(vecs.shape[0])) if index_subset is None else list(index_subset)
    sub = vecs[idx]
    if len(idx) == 1:
        return [[idx[0]]]
    model = AgglomerativeClustering(
        n_clusters=None, metric="cosine", linkage="complete",
        distance_threshold=1.0 - threshold)
    labels = model.fit_predict(sub.astype(np.float64))
    out = {}
    for pos, lab in enumerate(labels):
        out.setdefault(int(lab), []).append(idx[pos])
    return list(out.values())


def scalable_clusters(vecs, threshold, max_component=4000, block=512,
                      texts=None, progress=None):
    """Complete-linkage clustering in bounded memory, at campaign scale.

    Two separate blow-ups have to be avoided, and the second one killed a run.

    1. **The distance matrix.** Complete linkage on 238,944 documents wants a
       238,944^2 float64 matrix: 456 GB. Avoided because a complete-link cluster
       is always a subset of a single-link component, so components can be found
       first and exact complete linkage run inside each one.

    2. **The pair list.** FWS-HQ-ES-2018-0006 contains a campaign of 27,807
       byte-identical documents. Every pair of them clears any threshold, which
       is 386,600,721 pairs, roughly 27.8 GB as Python tuples. The first version
       materialised that list and the OS killed the process with no traceback.
       `lsh_candidate_pairs` has carried a bucket cap for this since it was
       written; the cosine path did not, which is the kind of gap that only
       shows up on a docket big enough to expose it.

       Fixed by never building the list: the similarity blocks feed union-find
       directly, so memory is O(n) in documents rather than O(n^2) in pairs.

    Inside an oversized component, exact duplicates are collapsed to one
    representative BEFORE complete linkage runs. That is not an approximation --
    identical documents cannot be separated by any threshold -- and it turns the
    27,807-document campaign into a single representative.
    """
    import collections

    import numpy as np

    import dedup

    n = vecs.shape[0]
    u = dedup.Union(n)
    edges = 0
    for s in range(0, n, block):
        e = min(s + block, n)
        sims = vecs[s:e] @ vecs.T
        for a in range(e - s):
            i = s + a
            js = np.nonzero(sims[a, i + 1:] >= threshold)[0]
            if js.size == 0:
                continue
            edges += int(js.size)
            # Union i with one member per DISTINCT existing component rather
            # than with every match. A mass campaign makes js enormous -- FDA
            # has 175,285 documents and a block-wide np.nonzero over it
            # produced tens of millions of indices at once, which killed the
            # process at row 42,496. After the first row of a campaign its
            # members already share a root, so this collapses to a handful of
            # unions per row while producing identical components.
            roots = {u.find(i)}
            for j in js + i + 1:
                r = u.find(int(j))
                if r not in roots:
                    u.union(i, int(j))
                    roots.add(u.find(i))
                    roots.discard(r)
            del js
        del sims
        if progress:
            progress(e, n)
    comps = u.groups()

    out, oversized = [], []
    for c in comps:
        if len(c) == 1:
            out.append(c)
            continue
        members = c
        if len(members) > max_component and texts is not None:
            # identical documents cannot be split by any threshold, so collapse
            # them to one representative first; exact, not approximate
            byhash = collections.defaultdict(list)
            for i in members:
                byhash[dedup.exact_key(texts[i])].append(i)
            reps = [g[0] for g in byhash.values()]
            if len(reps) <= max_component:
                for sub in complete_link_clusters(vecs, threshold, index_subset=reps):
                    expanded = []
                    for r in sub:
                        expanded.extend(byhash[dedup.exact_key(texts[r])])
                    out.append(expanded)
                continue
            oversized.append(len(members))
            out.append(members)
        elif len(members) > max_component:
            oversized.append(len(members))
            out.append(members)
        else:
            out.extend(complete_link_clusters(vecs, threshold, index_subset=members))
    return out, {"edges": edges, "components": len(comps),
                 "oversized_components": oversized}


def _agree_block(sigs, s, e):
    """Fraction of matching permutations between rows [s:e) and all rows.

    Accumulates one permutation at a time. The obvious vectorisation,
    `sigs[s:e, None, :] == sigs[None, :, :]`, materialises a
    (block x n x num_perm) boolean array before reducing it -- 11.5 GB per
    block at FDA-2021-N-1349's 175,285 documents, which killed a run. Summing
    per permutation holds one (block x n) array instead, so memory is flat in
    num_perm.
    """
    import numpy as np
    n = sigs.shape[0]
    acc = np.zeros((e - s, n), dtype=np.uint8)      # 128 perms fits a uint8
    for p in range(sigs.shape[1]):
        acc += (sigs[s:e, p][:, None] == sigs[None, :, p])
    return acc.astype(np.float32) / sigs.shape[1]


def minhash_complete_clusters(sigs, threshold, max_component=4000, block=256,
                              texts=None):
    """Complete-linkage clustering on MinHash signatures.

    Exists so the near rung is clustered the same way as the semantic rung.
    Phase 1 reports its headline comparison as complete linkage on both, and
    `run_docket` was using connected components for near, so the per-docket
    Phase 2 output was not reproducing the comparison it cites.

    Signature agreement IS the Jaccard estimate, so similarity here is the
    fraction of matching permutations. Memory discipline mirrors
    `scalable_clusters`: stream into union-find, never build a pair list, and
    collapse exact-duplicate texts to one representative inside an oversized
    component.
    """
    import collections

    import numpy as np

    import dedup

    n = sigs.shape[0]
    u = dedup.Union(n)

    # Candidates from LSH, not all pairs. All-pairs is O(n^2 * num_perm): at
    # FDA-2021-N-1349's 175,287 documents that is ~3.9e12 comparisons and it
    # had run 46 minutes without finishing; ED-2021-OCR-0166 would be twice
    # that. LSH is the standard answer and was already being computed for the
    # candidate set.
    #
    # The cost is recall, and it should be stated rather than assumed. With 32
    # bands of 4 rows, a pair at the operating threshold 0.625 is detected with
    # probability 1 - (1 - 0.625^4)^32 = 99.5% at the production signature
    # length of 128. So a handful of true
    # near-duplicates are missed, which makes the near rung's collapse a slight
    # UNDER-estimate -- the conservative direction, and the same direction as
    # the precision-first operating point.
    # Band the signature to whatever length it actually has. Hard-coding
    # 32x4 asserts out on a 64-permutation signature, which is exactly what a
    # test used -- the production path never saw it because it always passes
    # 128.
    rows_per_band = 4
    bands = max(1, sigs.shape[1] // rows_per_band)
    for i, j in dedup.lsh_candidate_pairs(sigs, bands=bands, rows=rows_per_band):
        if u.find(i) == u.find(j):
            continue
        if float(np.mean(sigs[i] == sigs[j])) >= threshold:
            u.union(i, j)

    from sklearn.cluster import AgglomerativeClustering
    out, oversized = [], []
    for c in u.groups():
        if len(c) <= 1:
            out.append(c)
            continue
        members = c
        if len(members) > max_component and texts is not None:
            byhash = collections.defaultdict(list)
            for i in members:
                byhash[dedup.exact_key(texts[i])].append(i)
            reps = [g[0] for g in byhash.values()]
            if len(reps) == 1:
                # every member of the component is the SAME text. No clustering
                # needed or possible -- AgglomerativeClustering requires two
                # samples, and this is what a 238,944-document docket with one
                # enormous uniform campaign actually produces.
                out.append(members)
                continue
            if len(reps) <= max_component:
                sub = sigs[reps]
                d = 1.0 - _agree_block(sub, 0, len(reps))
                np.fill_diagonal(d, 0.0)
                lab = AgglomerativeClustering(
                    n_clusters=None, metric="precomputed", linkage="complete",
                    distance_threshold=1.0 - threshold).fit_predict(d.astype(np.float64))
                g = {}
                for pos, l in enumerate(lab):
                    g.setdefault(int(l), []).append(reps[pos])
                for grp in g.values():
                    expanded = []
                    for r in grp:
                        expanded.extend(byhash[dedup.exact_key(texts[r])])
                    out.append(expanded)
                continue
            oversized.append(len(members))
            out.append(members)
            continue
        if len(members) > max_component:
            oversized.append(len(members))
            out.append(members)
            continue
        sub = sigs[members]
        d = 1.0 - _agree_block(sub, 0, len(members))
        np.fill_diagonal(d, 0.0)
        lab = AgglomerativeClustering(
            n_clusters=None, metric="precomputed", linkage="complete",
            distance_threshold=1.0 - threshold).fit_predict(d.astype(np.float64))
        g = {}
        for pos, l in enumerate(lab):
            g.setdefault(int(l), []).append(members[pos])
        out.extend(g.values())
    return out
