"""Read the public mirrulations S3 bucket over plain HTTPS.

No credentials, no aws CLI, no boto3. The bucket allows anonymous
ListObjectsV2, which is the only operation the coverage check needs.
"""
import re
import time
import urllib.parse
import urllib.request

BUCKET_URL = "https://mirrulations.s3.amazonaws.com/"
_KEY = re.compile(r"<Key>([^<]+)</Key>")
_ENTRY = re.compile(r"<Key>([^<]+)</Key>\s*<LastModified>([^<]+)</LastModified>")
_TOKEN = re.compile(r"<NextContinuationToken>([^<]+)</NextContinuationToken>")
_TRUNC = re.compile(r"<IsTruncated>(true|false)</IsTruncated>")


def _get(params, retries=4):
    url = BUCKET_URL + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/xml"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:          # transient network / 503 slowdown
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"S3 list failed after {retries} tries: {last}")


def parse_page(xml):
    """Return (keys, next_token). next_token is None on the last page."""
    keys = _KEY.findall(xml)
    truncated = bool(_TRUNC.search(xml)) and _TRUNC.search(xml).group(1) == "true"
    token = _TOKEN.search(xml)
    return keys, (token.group(1) if (truncated and token) else None)


def list_keys(prefix, suffix=None, on_page=None):
    """Yield every key under prefix, optionally filtered by suffix."""
    token = None
    pages = 0
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        keys, token = parse_page(_get(params))
        pages += 1
        for k in keys:
            if suffix is None or k.endswith(suffix):
                yield k
        if on_page:
            on_page(pages, len(keys))
        if not token:
            return


def list_entries(prefix, suffix=None):
    """Yield (key, last_modified) pairs. Same walk as list_keys, one extra field.

    Kept separate so the common case does not pay for the second capture, but
    used by the coverage pass so a 500,000-key docket is listed once, not twice.
    """
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        xml = _get(params)
        for k, lm in _ENTRY.findall(xml):
            if suffix is None or k.endswith(suffix):
                yield k, lm
        _, token = parse_page(xml)
        if not token:
            return


def count_keys(prefix, suffix=None):
    n = 0
    for _ in list_keys(prefix, suffix):
        n += 1
    return n
