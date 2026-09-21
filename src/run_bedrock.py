"""Run rung 3 on Bedrock Titan, as the comparison arm to local MiniLM.

TWO ARMS, because Titan differs from MiniLM in two ways at once and conflating
them would answer neither question:

  matched  : chunked to 180 words and mean-pooled, exactly as MiniLM is, so the
             only variable is MODEL CAPACITY (22M params vs Titan).
  native   : the whole document up to Titan's 8,192-token window in one call,
             so the variable is CONTEXT LENGTH.

Phase 1 found embeddings beat MinHash by 0.3 points at constrained thresholds.
The live objection is that this used a 22M-parameter model with a 256-token
window. If Titan lands in the same place in the matched arm, that objection is
answered. If the native arm moves it, the finding was about context, not model.

The threshold is re-selected per arm on the same human labels: cosine 0.9641
is a MiniLM number and means nothing on Titan.
"""
import json
import os
import sys
import time

import numpy as np

MODEL = os.environ.get("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
DIMS = 1024
MAX_TOKENS = 8000          # Titan's window is 8,192; leave headroom
CHARS_PER_TOKEN = 4


def _client():
    import boto3
    return boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def embed_one(text, client=None, retries=6, max_shrinks=24):
    """Embed one string, shrinking on rejection rather than trusting a constant.

    A fixed chars-per-token budget does not hold. 8,000 tokens estimated at 4
    chars each produced a document Titan counted as 8,316, over its 8,192
    limit, and the run died. Regulatory prose is dense in short tokens --
    section numbers, units, hyphenated terms -- so the ratio varies per
    document. Shrinking until it fits is correct for every document rather
    than correct on average.

    Shrinking is counted SEPARATELY from throttle retries. Sharing one budget
    meant a very long document ran out of attempts while still too long, which
    is a different failure wearing the same exception.
    """
    client = client or _client()
    budget = MAX_TOKENS * CHARS_PER_TOKEN
    shrinks = 0
    attempt = 0
    while True:
        body = json.dumps({"inputText": text[:budget] or " ",
                           "dimensions": DIMS, "normalize": True})
        try:
            r = client.invoke_model(modelId=MODEL, body=body)
            return np.array(json.loads(r["body"].read())["embedding"], dtype=np.float32)
        except Exception as exc:
            msg = str(exc)
            if "Too many input tokens" in msg or "expected maxLength" in msg:
                shrinks += 1
                if shrinks > max_shrinks:
                    raise
                budget = max(64, budget // 2)
                continue
            attempt += 1
            if attempt >= retries:
                raise
            # throttling is expected at 2,000 req/min; back off rather than
            # lose the document
            time.sleep(min(2 ** attempt, 20))


def embed_matched(texts, workers=8, progress=None):
    """Chunked and mean-pooled the same way MiniLM is."""
    import concurrent.futures as cf

    import embed as local
    client = _client()
    out = np.zeros((len(texts), DIMS), dtype=np.float32)

    def one(i):
        chunks = local.chunk(texts[i])
        vs = [embed_one(c, client) for c in chunks if c.strip()]
        if not vs:
            return i, np.zeros(DIMS, dtype=np.float32)
        v = np.mean(vs, axis=0)
        return i, v / max(np.linalg.norm(v), 1e-9)

    done = 0
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, v in ex.map(one, range(len(texts))):
            out[i] = v
            done += 1
            if progress and done % 200 == 0:
                progress(done, len(texts))
    return out


def embed_native(texts, workers=8, progress=None):
    """Whole document in one call, up to Titan's own window."""
    import concurrent.futures as cf
    client = _client()
    out = np.zeros((len(texts), DIMS), dtype=np.float32)

    def one(i):
        t = texts[i].strip() or " "
        return i, embed_one(t, client)

    done = 0
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, v in ex.map(one, range(len(texts))):
            n = np.linalg.norm(v)
            out[i] = v / max(n, 1e-9)
            done += 1
            if progress and done % 200 == 0:
                progress(done, len(texts))
    return out


if __name__ == "__main__":
    import clean, corpus
    docket = sys.argv[1]
    arm = sys.argv[2] if len(sys.argv) > 2 else "matched"
    rows = [r for r in corpus.load(docket) if r["source"] != "none"]
    texts = [clean.clean(r["text"]) for r in rows]
    keep = [i for i, t in enumerate(texts) if t.strip()]
    kt = [texts[i] for i in keep]
    sys.stderr.write(f"{docket} [{arm}]: {len(kt)} documents\n")
    p = lambda d, t: (sys.stderr.write(f"  {d}/{t}\r"), sys.stderr.flush())
    t0 = time.time()
    v = (embed_matched if arm == "matched" else embed_native)(kt, progress=p)
    np.save(f"data/{docket}/vecs_titan_{arm}.npy", v)
    print(json.dumps({"docket": docket, "arm": arm, "n": len(kt),
                      "dims": int(v.shape[1]), "seconds": round(time.time() - t0, 1)}))
