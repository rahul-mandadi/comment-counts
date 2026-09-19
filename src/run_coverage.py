"""One listing pass per docket, answering every keyless coverage question.

The big dockets are ~240,000 objects, so each prefix is walked exactly once and
every measure is accumulated in that walk.
"""
import collections
import json
import sys

import dockets
import keys
import mirror


def walk(docket_id, agency):
    base = f"raw-data/{agency}/{docket_id}/text-{docket_id}/"
    out = {"docket": docket_id, "agency": agency}

    # --- comment records -------------------------------------------------
    ckeys, newest = [], ""
    for k, lm in mirror.list_entries(base + "comments/", ".json"):
        ckeys.append(k)
        if lm > newest:
            newest = lm
    dedup = keys.dedupe(ckeys)
    out["comment_objects"] = len(ckeys)
    out["comment_records"] = len(dedup)
    out["duplicate_objects"] = len(ckeys) - len(dedup)
    out["mirror_newest_write"] = newest

    # --- numbering density ----------------------------------------------
    dkeys = list(mirror.list_keys(base + "documents/", ".json"))
    docs = set(keys.dedupe(dkeys))
    out["documents"] = len(docs)
    nums = {n for n in (keys.sequence_number(c) for c in dedup) if n is not None}
    nums |= {n for n in (keys.sequence_number(c) for c in docs) if n is not None}
    lo, hi = min(nums), max(nums)
    holes = sorted(set(range(lo, hi + 1)) - nums)
    runs, start, prev = [], None, None
    for n in holes:
        if prev is None or n != prev + 1:
            if start is not None:
                runs.append((start, prev))
            start = n
        prev = n
    if start is not None:
        runs.append((start, prev))
    out["id_range"] = [lo, hi]
    out["holes"] = len(holes)
    out["hole_share"] = round(len(holes) / (hi - lo + 1), 4)
    out["longest_hole_run"] = max((b - a + 1 for a, b in runs), default=0)
    out["holes_in_runs_of_5_plus"] = sum(b - a + 1 for a, b in runs if b - a + 1 >= 5)

    # --- attachments and their extraction --------------------------------
    per_ext = collections.defaultdict(set)
    with_binary, binary_files, exts = set(), 0, collections.Counter()
    for k in mirror.list_keys(dockets.attachments_prefix(docket_id, agency)):
        if k.endswith("/"):
            continue
        cid = keys.comment_id(k.rsplit("_attachment", 1)[0] + ".json")
        with_binary.add(cid)
        binary_files += 1
        ext = k.rsplit(".", 1)[-1].lower() if "." in k.rsplit("/", 1)[-1] else "(none)"
        exts[ext] += 1
        per_ext[cid].add(ext)

    with_text, text_files = set(), 0
    for k in mirror.list_keys(dockets.extracted_prefix(docket_id, agency), ".txt"):
        cid = keys.comment_id(k.rsplit("_attachment", 1)[0] + ".json")
        with_text.add(cid)
        text_files += 1

    unextracted = with_binary - with_text
    fmt_only = {c for c in unextracted if "pdf" not in per_ext.get(c, set())}
    out.update({
        "comments_with_attachment": len(with_binary),
        "attachment_files": binary_files,
        "pdf_files": exts.get("pdf", 0),
        "extracted_text_files": text_files,
        "comments_with_extracted_text": len(with_text),
        "unextracted_pdf_comments": len(unextracted - fmt_only),
        "unextracted_nonpdf_only_comments": len(fmt_only),
        "extracted_without_binary": len(with_text - with_binary),
        "attachment_ext_counts": dict(exts.most_common(10)),
        "attachment_rate": round(len(with_binary) / max(1, len(dedup)), 4),
    })
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    a = dict((x[0], x[1]) for x in dockets.DOCKETS)[d]
    print(json.dumps(walk(d, a)))
