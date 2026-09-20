# Coverage check on the mirrulations mirror

Run 2026-09-18. This is the gate the spec set before any pipeline is built:
**a silently partial mirror would bias every ratio in the project and look like a
finding.** It found two real defects and one open question.

Everything below is measured from the public bucket with no credentials. The
commands are in `src/`, the raw output in `out/coverage.json`.

## What the publisher claims

The AWS Open Data registry entry for `mirrulations` states an **hourly** update
frequency and says the system "has successfully downloaded all historic data and
continues to run and collect data each hour". License is Public Domain Mark 1.0;
the requested citation is *"mirrulations was accessed on DATE from
https://registry.opendata.aws/mirrulations."*

That claim is testable, so it was tested.

## Finding 1: counting objects is not counting comments

| docket | objects | distinct records | duplicate objects |
|---|---|---|---|
| ED-2021-OCR-0166 | 238,945 | 238,944 | 1 |
| **FDA-2021-N-1349** | **198,312** | **175,313** | **22,999 (11.6% of objects)** |
| FWS-HQ-ES-2018-0006 | 64,019 | 64,019 | 0 |
| EPA-HQ-OAR-2013-0602 | 19,319 | 19,319 | 0 |
| EPA-HQ-OAR-2021-0317 | 3,639 | 3,578 | 61 |
| OSHA-2010-0034 | 1,406 | 1,406 | 0 |

The mirror stores some records twice, as `<ID>.json` and `<ID>(1).json`. Anyone
counting objects reads FDA-2021-N-1349 as **198,312 comments when it holds
175,313** -- a 13.1% overstatement on the second-largest docket in the corpus.
The spec's own docket table had the inflated number in it.

Two things were checked rather than assumed:

- **No record exists only as a suffixed copy.** Orphan count is 0 on all six
  dockets, so collapsing the suffix never drops a comment.
- **The copies are not identical.** `FDA-2021-N-1349-53031` differs: the suffixed
  copy has `modifyDate` 2023-10-03 against the plain copy's 2023-02-06 and carries
  a `category` the plain copy leaves null. So the suffixed copy is the later
  re-fetch and is the one to read. `src/keys.py` encodes that, with tests.

## Finding 2: the mirror is missing comments on the older dockets

regulations.gov numbers documents and comments in **one sequence** per docket, so
the union of the mirror's comment IDs and document IDs should be a dense run. Every
hole is a number the government issued that the mirror does not hold.

| docket | records | documents | id span | holes | hole share | longest run |
|---|---|---|---|---|---|---|
| ED-2021-OCR-0166 | 238,944 | 2 | 238,989 | 43 | 0.02% | 3 |
| FDA-2021-N-1349 | 175,313 | 576 | 175,894 | 5 | 0.00% | 2 |
| FWS-HQ-ES-2018-0006 | 64,019 | 6 | 64,027 | 2 | 0.00% | 1 |
| **EPA-HQ-OAR-2013-0602** | 19,319 | 2,946 | 37,425 | **15,160** | **40.51%** | 313 |
| EPA-HQ-OAR-2021-0317 | 3,578 | 509 | 4,068 | 0 | 0.00% | 0 |
| **OSHA-2010-0034** | 1,406 | 2,475 | 4,355 | **474** | **10.88%** | 75 |

**The probe was calibrated against the truth once.** For OSHA-2010-0034 the
regulations.gov API reports **1,878** comments; the mirror holds **1,406**, so
**472** are missing. This probe independently finds **474** holes. Agreement to
0.4%, on the one docket where the answer was available separately, is why the
probe is trusted where it is not.

The hole *shape* says the same thing. Holes are not scattered singletons, which is
what withdrawn submissions would look like. They are long runs: **451 of the 460
runs on EPA-HQ-OAR-2013-0602 are bounded by a comment on both sides**, and the
longest is 313 consecutive numbers. That is a fetch that stopped, not a numbering
convention.

**This lands on the pilot docket, which is the problem.** If the calibration holds,
EPA-HQ-OAR-2013-0602 is missing on the order of 15,160 records and the mirror holds
roughly **56%** of it. Phase 0's headline figures -- 19,319 records, 4,360,986
submissions, 225.7x -- were computed on that partial set.

**What that does and does not do to Phase 0.** The 225.7x ratio is a ratio of two
numbers from the same partial set, so it is not obviously biased in either
direction, and the qualitative finding (the record publishes two counts, far apart,
without marking which is which) does not depend on holding every record. But the
absolute figures are not the docket's figures, and must not be reported as if they
were until this is settled.

### CONFIRMED 2026-09-20 against regulations.gov's own totals

A registered key arrived and the probe was checked against the truth on all six.

| docket | mirror | official | missing | holes predicted | share | probe error |
|---|---|---|---|---|---|---|
| ED-2021-OCR-0166 | 238,944 | 238,987 | 43 | 43 | 100.0% | **0** |
| FDA-2021-N-1349 | 175,313 | 175,317 | 4 | 5 | 100.0% | +1 |
| FWS-HQ-ES-2018-0006 | 64,019 | 64,021 | 2 | 2 | 100.0% | **0** |
| **EPA-HQ-OAR-2013-0602** | 19,319 | **34,479** | **15,160** | **15,160** | **56.0%** | **0** |
| **EPA-HQ-OAR-2021-0317** | 3,578 | 3,578 | 0 | 0 | **100.0%** | **0** |
| OSHA-2010-0034 | 1,406 | 1,878 | 472 | 474 | 74.9% | +2 |
| **total** | **502,579** | **518,260** | **15,681** | | **96.97%** | **3** |

**The keyless probe predicted the answer to within 3 records out of 518,260.** Four dockets
exact, two within two. Numbering-hole density is therefore a sound coverage estimate for any
docket on this mirror, and it costs no API quota, which matters because the rate-limited API
is the reason this project reads the mirror in the first place.

**Two results that change what can be claimed:**

1. **The pilot docket is 56.0% complete**, exactly as estimated. 19,319 of 34,479. Phase 0's
   absolute figures are figures for a bit over half a docket and must never be quoted as the
   docket's.
2. **EPA-HQ-OAR-2021-0317 is 3,578 of 3,578 -- provably complete.** Phase 1 ran on a docket
   with no missing records, so its 233.99 submissions per record is a whole-docket measurement
   rather than an estimate.

**Previously unsettled, now resolved.** Confirming the EPA number requires
regulations.gov's own `totalElements` for that docket. api.data.gov's shared
DEMO_KEY rate-limited out after three requests, and the public regulations.gov web
front end returns 403 to scripted access for every ID, real or invented, so it
cannot serve as a control either. A free registered key resolves it:

```bash
export REGULATIONS_GOV_API_KEY=...        # https://open.gsa.gov/api/regulationsgov/
PYTHONPATH=src python3 src/coverage.py    # fills in official_records and missing
```

## Finding 3: attachment extraction is essentially complete

This was the fourth open question in the spec, and it is the one that came back
clean. It matters because Phase 0 measured that **84.3% of comment bodies on the
pilot docket say only "See attached"** -- the attachment *is* the comment, so a
partial extraction would be a biased subset in the same way OCR failures would.

| docket | comments w/ attachment | attach rate | PDFs | extracted .txt | unextracted PDF comments |
|---|---|---|---|---|---|
| ED-2021-OCR-0166 | 7,370 | 3.1% | 7,532 | 7,532 | 0 |
| FDA-2021-N-1349 | 836 | 0.5% | 941 | 941 | 0 |
| FWS-HQ-ES-2018-0006 | 459 | 0.7% | 576 | 576 | 0 |
| EPA-HQ-OAR-2013-0602 | 16,488 | 85.4% | 18,239 | 18,239 | 0 |
| EPA-HQ-OAR-2021-0317 | 2,838 | 79.3% | 3,230 | 3,222 | **6** |
| OSHA-2010-0034 | 647 | 46.0% | 1,180 | 1,180 | 0 |

**Every PDF has an extracted text file except 8 files on one docket.** There is no
extracted text with no source binary, so the derived layer is not inventing
anything either.

**The real gap is format, not failure.** 385 comments across the corpus carry an
attachment and no extracted text because none of their attachments is a PDF:
docx, png, jpg, rtf, xlsx, wpd, and one `.mov`. pdfminer is a PDF tool, so this is
expected rather than broken -- but it is **not random**. On ED-2021-OCR-0166 the
unextracted set includes 429 `.png` and 329 `.jpg`, which are scans and photographs
of letters. Those are disproportionately likely to be individually written rather
than campaign-supplied, which is precisely the population this project is trying to
separate. Recorded as a known bound, not fixed here.

**And the attachment rate itself is a finding worth keeping.** It spans 0.5% to
85.4%. The two EPA dockets sit at 85.4% and 79.3% while ED, FDA and FWS sit under
3.2%. Comment *systems* differ by agency, exactly as the docket selection assumed,
and any method that reads the `comment` field will behave completely differently
across these six.

## Finding 4: freshness is fine for this corpus, and the claim is not

Newest object write per docket: five of the six are **2025-04-13 or 2025-04-14**,
and EPA-HQ-OAR-2021-0317 is **2025-07-29**. Today is 2026-09-18.

For *this* corpus that is harmless -- every comment period here closed years ago,
so a closed docket having no new writes is correct behaviour, not staleness, and
the "hourly" claim is about incoming data rather than backfill repair.

It does mean the holes in Finding 2 are **not going to close on their own**. They
were written in an April 2025 bulk backfill that has not been revisited in
seventeen months.

## Verdict

| spec question | answer |
|---|---|
| 1. Does the mirror carry these dockets, completely? | Carries all six, **96.97% of records overall, confirmed against regulations.gov**. Complete on four; OSHA-2010-0034 is 74.9% and the pilot EPA-HQ-OAR-2013-0602 is 56.0%. |
| 2. How far behind live? | 17 months since last write, irrelevant for six closed dockets. |
| 3. Terms and citation | Public Domain Mark 1.0; cite as the registry specifies. |
| 4. Is `derived-data` extraction complete? | For PDFs, yes: 8 unextracted files in 31,698. For non-PDF attachments, no, and the gap skews toward scanned individual letters. |

**Proceed, with two changes.** Record counts must go through `src/keys.py`, never
through an object count. And the pilot docket's absolute figures are provisional
until the API confirms its true record count.
