"""Coverage check: is the mirror complete for the dockets this project selected?

Two questions, answered separately because they fail differently:

  1. RECORD coverage  -- does the mirror hold every comment record the docket has?
     Checked against regulations.gov's own totalElements. Needs an API key.
  2. ATTACHMENT coverage -- of the comments that carry an attachment, how many
     have pre-extracted text under derived-data? Checked entirely inside the
     mirror, so it needs no key.

Question 2 matters as much as question 1 here. Phase 0 measured that 84.3% of
comment bodies on the pilot docket say only "See attached", so the attachment
IS the comment. A partial extraction is a biased subset in exactly the way the
spec warned about, and it would silently drop the longest, most substantive
submissions -- the ones most likely to be scanned PDFs that pdfminer fails on.
"""
import json
import re
import sys

import dockets
import keys
import mirror

_ID = re.compile(r"([A-Z][A-Za-z0-9_-]*-\d{4}-[A-Za-z0-9-]+-\d+)")


def comment_id_from_key(key):
    """Mirror keys are <...>/<COMMENT-ID>.json or <...>/<COMMENT-ID>/<file>."""
    m = _ID.search(key.rsplit("/", 1)[-1]) or _ID.search(key)
    return m.group(1) if m else None


def mirror_record_ids(docket_id, agency):
    """Distinct comment IDs, not objects. See keys.py for why they differ."""
    prefix = dockets.comments_prefix(docket_id, agency)
    return set(keys.dedupe(mirror.list_keys(prefix, ".json")))


def attachment_coverage(docket_id, agency):
    """Comments with >=1 binary attachment vs comments with >=1 extracted txt."""
    import collections
    with_binary, binary_files = set(), 0
    exts = collections.Counter()
    pdf_files, nonpdf_only = set(), collections.Counter()
    per_comment_ext = collections.defaultdict(set)
    for k in mirror.list_keys(dockets.attachments_prefix(docket_id, agency)):
        if k.endswith("/"):
            continue
        cid = comment_id_from_key(k)
        if cid:
            with_binary.add(cid)
            binary_files += 1
            ext = k.rsplit(".", 1)[-1].lower() if "." in k.rsplit("/", 1)[-1] else "(none)"
            exts[ext] += 1
            per_comment_ext[cid].add(ext)
            if ext == "pdf":
                pdf_files.add(k)

    with_text, text_files = set(), 0
    for k in mirror.list_keys(dockets.extracted_prefix(docket_id, agency), ".txt"):
        cid = comment_id_from_key(k)
        if cid:
            with_text.add(cid)
            text_files += 1

    unextracted = with_binary - with_text
    # a comment whose only attachments are non-PDF is a FORMAT gap, not an
    # extraction failure -- pdfminer is a PDF tool. Separate the two, because
    # only the second is evidence the mirror's derived layer is unreliable.
    fmt_gap = {c for c in unextracted if "pdf" not in per_comment_ext.get(c, set())}
    return {
        "attachment_ext_counts": dict(exts.most_common(8)),
        "unextracted_pdf_comments": len(unextracted - fmt_gap),
        "unextracted_nonpdf_only_comments": len(fmt_gap),
        "comments_with_attachment": len(with_binary),
        "attachment_files": binary_files,
        "comments_with_extracted_text": len(with_text),
        "extracted_text_files": text_files,
        "attached_but_unextracted": len(with_binary - with_text),
        "extracted_without_binary": len(with_text - with_binary),
        "_unextracted_pdf_sample": sorted(unextracted - fmt_gap)[:10],
    }


def check(docket_id, agency, note="", want_official=True):
    row = {"docket": docket_id, "agency": agency, "note": note}
    ids = mirror_record_ids(docket_id, agency)
    row["mirror_records"] = len(ids)

    if want_official:
        try:
            import official
            o = official.comment_total(docket_id)
            row["official_records"] = o["total"]
            if o["total"]:
                row["mirror_share"] = round(len(ids) / o["total"], 4)
                row["missing"] = o["total"] - len(ids)
        except Exception as exc:
            row["official_records"] = None
            row["official_error"] = str(exc)[:160]

    row.update(attachment_coverage(docket_id, agency))
    return row


def main(argv):
    want_official = "--no-official" not in argv
    only = [a for a in argv[1:] if not a.startswith("-")]
    rows = []
    for d, a, note in dockets.DOCKETS:
        if only and d not in only:
            continue
        sys.stderr.write(f"... {d}\n")
        sys.stderr.flush()
        rows.append(check(d, a, note, want_official))
        print(json.dumps(rows[-1]), flush=True)
    return rows


if __name__ == "__main__":
    main(sys.argv)
