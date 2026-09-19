# What does a public comment count measure?

One federal rule drew **4,360,986 comments**. It also drew **19,319**. Both numbers are
in the official record, both are correct, and nothing marks which one you are reading.

Status: **Phase 1, coverage verified.** See `docs/coverage.md`.
Spec and rationale: `~/dev/Job_search/docs/project_comment_counts_spec.md`.

## Data

The public `s3://mirrulations` mirror of regulations.gov, run by Moravian University
Computer Science. No credentials needed; this repo reads it over plain HTTPS.

> mirrulations was accessed on 2026-09-18 from https://registry.opendata.aws/mirrulations.

Licensed Public Domain Mark 1.0.

## Running the checks

```bash
PYTHONPATH=src python3 src/run_coverage.py <DOCKET-ID>   # one docket, keyless
python3 -m pytest tests/ -q
```

The record-coverage confirmation needs a free regulations.gov API key, which this repo
never stores:

```bash
export REGULATIONS_GOV_API_KEY=...        # https://open.gsa.gov/api/regulationsgov/
PYTHONPATH=src python3 src/coverage.py
```

## What this does not do

It measures distinctness, not authenticity, and a deduplicated count is a count of
arguments rather than of people. Organised participation is participation. The six
dockets are chosen, not sampled.
