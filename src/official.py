"""regulations.gov's own comment count per docket -- the number the mirror
is being checked against.

Uses api.data.gov's public DEMO_KEY by default so the check runs with no
setup. DEMO_KEY is rate limited to 30 requests/hour per IP, which is fine
for one request per docket and nothing else. Set REGULATIONS_GOV_API_KEY
to use a real key.
"""
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://api.regulations.gov/v4"


def api_key():
    return os.environ.get("REGULATIONS_GOV_API_KEY", "DEMO_KEY")


def _get(path, params, retries=3):
    params = dict(params)
    params["api_key"] = api_key()
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RuntimeError(
                    "rate limited by api.data.gov. DEMO_KEY allows 30 requests/hour; "
                    "set REGULATIONS_GOV_API_KEY to a registered key."
                ) from exc
            last = exc
            time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"regulations.gov request failed: {last}")


def comment_total(docket_id):
    """meta.totalElements for every comment filed on this docket.

    page[size]=5 rather than 0 because the API rejects a zero page size; the
    payload is discarded and only the metadata count is used.
    """
    doc = _get("comments", {"filter[docketId]": docket_id, "page[size]": 5})
    meta = doc.get("meta", {})
    return {
        "total": meta.get("totalElements"),
        "total_pages": meta.get("totalPages"),
        "sample_ids": [d["id"] for d in doc.get("data", [])],
    }
