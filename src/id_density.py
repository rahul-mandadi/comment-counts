"""A keyless proxy for record coverage.

regulations.gov numbers every item in a docket -- documents and comments
together -- in one sequence, `<DOCKET>-NNNN`. So the union of the mirror's
comment IDs and its document IDs should be a dense run from 1 to the maximum.
Every hole is an item regulations.gov issued a number for and the mirror does
not hold.

This is a PROXY and must be reported as one: a hole can also be a withdrawn
submission or a number issued and never used, so the hole count is an UPPER
bound on what is missing.

It was calibrated against the real answer once. On OSHA-2010-0034 the API
reports 1,878 comments, the mirror holds 1,406, so 472 are missing -- and this
probe independently finds 474 holes. Agreement to 0.4% on a case where the
truth was known separately is why the proxy is trusted on the dockets where it
is not.
"""
import sys

import dockets
import keys
import mirror

def _nums(prefix):
    """Sequence numbers of the DISTINCT records under prefix.

    Goes through keys.dedupe rather than parsing the filename directly: the
    mirror stores some records twice as `<ID>(1).json`, and a naive regex both
    misses those records and, on FDA-2021-N-1349, would have reported 175,313
    where a per-object count says 198,312.
    """
    out = set()
    for cid in keys.dedupe(mirror.list_keys(prefix, ".json")):
        n = keys.sequence_number(cid)
        if n is not None:
            out.add(n)
    return out


def density(docket_id, agency):
    base = f"raw-data/{agency}/{docket_id}/text-{docket_id}/"
    comments = _nums(base + "comments/")
    documents = _nums(base + "documents/")
    union = comments | documents
    if not union:
        return {"docket": docket_id, "error": "no numbered objects"}
    lo, hi = min(union), max(union)
    holes = sorted(set(range(lo, hi + 1)) - union)

    runs = []
    start = prev = None
    for n in holes:
        if prev is None or n != prev + 1:
            if start is not None:
                runs.append((start, prev))
            start = n
        prev = n
    if start is not None:
        runs.append((start, prev))

    clustered = sum(b - a + 1 for a, b in runs if b - a + 1 >= 5)
    return {
        "docket": docket_id,
        "comments": len(comments),
        "documents": len(documents),
        "id_range": [lo, hi],
        "slots": hi - lo + 1,
        "holes": len(holes),
        "hole_share": round(len(holes) / (hi - lo + 1), 4),
        "hole_runs": len(runs),
        "longest_run": max((b - a + 1 for a, b in runs), default=0),
        # scattered holes look like withdrawals; long runs look like a fetch
        # that stopped. The shape is the diagnosis, not the count.
        "ids_in_runs_of_5_plus": clustered,
    }


if __name__ == "__main__":
    import json
    only = sys.argv[1:]
    for d, a, _ in dockets.DOCKETS:
        if only and d not in only:
            continue
        sys.stderr.write(f"... {d}\n"); sys.stderr.flush()
        print(json.dumps(density(d, a)), flush=True)
