"""Pull one docket's comment records and attachment text out of the mirror.

Writes two files under data/<DOCKET>/:
  comments.jsonl  -- one record per DISTINCT comment (see keys.py), metadata + body
  attachments.jsonl -- one row per extracted attachment text file

Concurrency is modest on purpose. The mirror is a university-run public good,
and this repo's parent project has a standing rule against hammering anyone's
host; 16 threads against S3 for a few thousand small objects is polite and is
also faster than the listing that precedes it.
"""
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import dockets
import keys
import mirror

BUCKET = "https://mirrulations.s3.amazonaws.com/"
FIELDS = ("comment", "organization", "firstName", "lastName", "city",
          "stateProvinceRegion", "country", "email", "postedDate", "docketId",
          "category", "fileFormats", "duplicateComments", "title",
          "documentType", "withdrawn", "modifyDate", "receiveDate",
          "pageCount", "govAgency", "subtype")


def _fetch(key, retries=4):
    url = BUCKET + urllib.parse.quote(key)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            if attempt == retries - 1:
                raise
            time.sleep(1.0 * (attempt + 1))


def fetch_comments(docket_id, agency, out_path, workers=16):
    prefix = dockets.comments_prefix(docket_id, agency)
    todo = keys.dedupe(mirror.list_keys(prefix, ".json"))
    sys.stderr.write(f"{docket_id}: {len(todo)} distinct comment records\n")

    def one(item):
        cid, key = item
        raw = json.loads(_fetch(key))
        attrs = raw.get("data", {}).get("attributes", {}) or {}
        row = {"id": cid, "_key": key}
        row.update({f: attrs.get(f) for f in FIELDS})
        rel = raw.get("data", {}).get("relationships", {}) or {}
        row["_has_attachment_rel"] = bool(rel.get("attachments", {}).get("data"))
        return row

    n = 0
    with open(out_path, "w") as fh, cf.ThreadPoolExecutor(workers) as ex:
        for row in ex.map(one, todo.items()):
            fh.write(json.dumps(row) + "\n")
            n += 1
            if n % 500 == 0:
                sys.stderr.write(f"  {n}\n"); sys.stderr.flush()
    return n


def fetch_attachment_text(docket_id, agency, out_path, workers=16):
    prefix = dockets.extracted_prefix(docket_id, agency)
    ks = list(mirror.list_keys(prefix, ".txt"))
    sys.stderr.write(f"{docket_id}: {len(ks)} extracted attachment texts\n")

    def one(k):
        name = k.rsplit("/", 1)[-1]
        stem = name[: -len("_extracted.txt")] if name.endswith("_extracted.txt") else name
        cid = keys.comment_id(stem.rsplit("_attachment", 1)[0] + ".json")
        body = _fetch(k).decode("utf-8", "replace")
        return {"id": cid, "file": name, "chars": len(body), "text": body}

    n = 0
    with open(out_path, "w") as fh, cf.ThreadPoolExecutor(workers) as ex:
        for row in ex.map(one, ks):
            fh.write(json.dumps(row) + "\n")
            n += 1
            if n % 500 == 0:
                sys.stderr.write(f"  {n}\n"); sys.stderr.flush()
    return n


if __name__ == "__main__":
    d = sys.argv[1]
    a = dict((x[0], x[1]) for x in dockets.DOCKETS)[d]
    out = os.path.join("data", d)
    os.makedirs(out, exist_ok=True)
    c = fetch_comments(d, a, os.path.join(out, "comments.jsonl"))
    t = fetch_attachment_text(d, a, os.path.join(out, "attachments.jsonl"))
    print(json.dumps({"docket": d, "comments": c, "attachment_texts": t}))
