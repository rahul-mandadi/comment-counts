"""Build the analysis corpus for one docket: one row per comment, with the text
that actually represents it and a record of where that text came from.
"""
import collections
import json
import os

import assemble


def load(docket_id, root="data"):
    d = os.path.join(root, docket_id)
    atts = collections.defaultdict(list)
    ap = os.path.join(d, "attachments.jsonl")
    if os.path.exists(ap):
        for line in open(ap):
            r = json.loads(line)
            atts[r["id"]].append((r["file"], r["text"]))

    rows = []
    for line in open(os.path.join(d, "comments.jsonl")):
        r = json.loads(line)
        parts = [t for _f, t in sorted(atts.get(r["id"], []))]
        text, source = assemble.assemble(r, parts)
        rows.append({
            "id": r["id"],
            "text": text,
            "source": source,
            "chars": len(text),
            "duplicateComments": r.get("duplicateComments") or 1,
            "organization": r.get("organization"),
            "postedDate": r.get("postedDate"),
            "city": r.get("city"),
            "stateProvinceRegion": r.get("stateProvinceRegion"),
            "category": r.get("category"),
            "n_attachments": len(parts),
            "body_chars": len(assemble.normalize_space(
                assemble.strip_html(r.get("comment") or ""))),
        })
    return rows


def summary(rows):
    src = collections.Counter(r["source"] for r in rows)
    usable = [r for r in rows if r["source"] != "none"]
    subs = sum(r["duplicateComments"] for r in rows)
    return {
        "records": len(rows),
        "submissions_official": subs,
        "submissions_per_record": round(subs / max(1, len(rows)), 2),
        "text_from_body": src["body"],
        "text_from_attachment": src["attachment"],
        "no_usable_text": src["none"],
        "no_usable_text_share": round(src["none"] / max(1, len(rows)), 4),
        "median_chars": sorted(r["chars"] for r in usable)[len(usable) // 2] if usable else 0,
        "records_with_dupes": sum(1 for r in rows if r["duplicateComments"] > 1),
    }
