"""Rung 3 on Bedrock batch, as the comparison arm to the local MiniLM run.

WHY this exists, since Phase 1 already produced an embedding result on a laptop
in 45 seconds. Phase 1's finding is that at matched precision, embeddings beat
forty lines of MinHash by 0.75 percentage points. The obvious objection is that
this was a 22M-parameter model with a 256-token window, so the result may be a
model-capacity artifact rather than a fact about the corpus. Titan Text
Embeddings V2 has an 8,192-token window. If it also lands near 9%, the negative
result is much harder to argue with. If it jumps, Phase 1's conclusion was about
the model and must be restated.

THE THRESHOLD DOES NOT TRANSFER, and this is the easiest way to get the
comparison wrong. Cosine 0.97 on MiniLM is not cosine 0.97 on Titan: different
models put different absolute similarity on the same pair. Comparing the two at
a shared numeric threshold would compare their calibration, not their ability.
So each model gets its threshold RE-SELECTED on the same labelled pairs, at
matched precision, and only then are the collapse numbers compared. See
`select_threshold`.

Batch rather than on-demand because there is no latency requirement and batch
is materially cheaper. Note two operational facts that are easy to trip on:
model access for Titan must be enabled by hand in the console once per account,
and Bedrock batch enforces a minimum record count per job, so a tiny pilot
docket may have to run on-demand instead.
"""
import json
import os
import time

MODEL_ID = os.environ.get("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")


def build_input_jsonl(ids, texts, dimensions=1024):
    """Bedrock batch input: one JSON object per line.

    recordId is how output rows are matched back; Bedrock does NOT guarantee
    output order, and assuming it does is a silent corruption that looks like
    a bad result rather than a bug.
    """
    lines = []
    for rid, text in zip(ids, texts):
        lines.append(json.dumps({
            "recordId": str(rid),
            "modelInput": {"inputText": text, "dimensions": dimensions,
                           "normalize": True},
        }))
    return "\n".join(lines) + "\n"


def parse_output_jsonl(raw, expected_ids=None):
    """Return {recordId: vector}, and refuse to guess about missing records."""
    out = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rid = row.get("recordId")
        body = row.get("modelOutput") or {}
        vec = body.get("embedding")
        if rid is None or vec is None:
            continue
        out[str(rid)] = vec
    if expected_ids is not None:
        missing = set(map(str, expected_ids)) - set(out)
        if missing:
            raise ValueError(
                f"{len(missing)} records have no embedding, e.g. {sorted(missing)[:3]}. "
                "Bedrock drops records it cannot process; filling them with zeros would "
                "make them look maximally dissimilar to everything, which reads as a "
                "finding. Fix the inputs or exclude these ids explicitly."
            )
    return out


def submit(store, ids, texts, role_arn, job_name=None, client=None, dimensions=1024):
    import boto3
    client = client or boto3.client("bedrock")
    job_name = job_name or f"comment-counts-{int(time.time())}"
    in_key = f"scratch/bedrock/{job_name}/input.jsonl"
    store.put_bytes(in_key, build_input_jsonl(ids, texts, dimensions).encode("utf-8"))
    resp = client.create_model_invocation_job(
        jobName=job_name,
        roleArn=role_arn,
        modelId=MODEL_ID,
        inputDataConfig={"s3InputDataConfig": {"s3Uri": store.uri(in_key)}},
        outputDataConfig={"s3OutputDataConfig":
                          {"s3Uri": store.uri(f"scratch/bedrock/{job_name}/out/")}},
    )
    return {"jobArn": resp["jobArn"], "jobName": job_name,
            "input": store.uri(in_key)}


def select_threshold(scores, labels, min_precision=1.0):
    """Lowest threshold whose precision still meets the bar.

    `scores` and `labels` are aligned: labels are True when the pair should
    merge. Lowest-qualifying rather than highest, because among thresholds that
    all satisfy the declared precision constraint the useful one is whichever
    keeps the most recall.
    """
    best = None
    for t in sorted(set(scores), reverse=True):
        tp = sum(1 for s, y in zip(scores, labels) if s >= t and y)
        fp = sum(1 for s, y in zip(scores, labels) if s >= t and not y)
        if tp + fp == 0:
            continue
        prec = tp / (tp + fp)
        if prec >= min_precision:
            best = t
    return best
