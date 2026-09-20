# What does a public comment count measure?

One federal rule drew **836,351 comments**. It also drew **3,578**. Both numbers are in the
official record, both are correct, and nothing on the page says which one you are reading.

**Status: Phase 1 complete** on EPA-HQ-OAR-2021-0317. 45 tests.

- `docs/coverage.md` — is the data source complete? (Two defects found; one docket is ~56% there.)
- `docs/phase1.md` — one docket end to end: three dedup rungs, labelled pairs, the result.

## The result in three lines

regulations.gov already collapses this docket **239.85x** through its own `duplicateComments`
field. Three rungs of deduplication, at an operating point chosen for precision before any
labelling, add **1.10x** on top. **99.96% of the total reduction was already official.**

At matched precision, semantic embeddings beat forty lines of MinHash by **0.75 percentage
points**. The expensive rung bought almost nothing.

## Data

The public `s3://mirrulations` mirror of regulations.gov, run by Moravian University
Computer Science. No credentials; this repo reads it over plain HTTPS.

> mirrulations was accessed on 2026-09-20 from https://registry.opendata.aws/mirrulations.

Public Domain Mark 1.0.

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python src/fetch_docket.py EPA-HQ-OAR-2021-0317
PYTHONPATH=src .venv/bin/python src/run_coverage.py EPA-HQ-OAR-2021-0317
.venv/bin/python -m pytest tests/ -q
```

Record coverage against regulations.gov's own totals needs a free key, never stored here:

```bash
export REGULATIONS_GOV_API_KEY=...        # https://open.gsa.gov/api/regulationsgov/
```

## What this does not do

It measures distinctness, not authenticity, and a deduplicated count is a count of arguments
rather than of people. Organised participation is participation. The dockets are chosen, not
sampled. **The pair labels are machine labels and have not been checked by a human** —
`labels/for_human.jsonl` is the subset that would fix that.
