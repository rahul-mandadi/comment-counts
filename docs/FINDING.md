# What does a public comment count measure?

**306,854 of 479,311 comment records on four federal dockets are byte-identical
duplicates of another record, and every one is published as a separate comment.**

That sentence needs no threshold, no embedding model, no similarity metric and no
human judgement. It is SHA-256 over whitespace-normalised text.

## The finding

| docket | agency | records | official duplicate count | byte-identical duplicates |
|---|---|---|---|---|
| FWS-HQ-ES-2018-0006 | Fish & Wildlife | 64,016 | **1.03x** | **59,129 (92.4%)** |
| FDA-2021-N-1349 | FDA | 175,285 | **1.00x** | **111,350 (63.5%)** |
| ED-2021-OCR-0166 | Education | 238,659 | **1.00x** | **135,823 (56.9%)** |
| OSHA-2010-0034 | OSHA | 1,351 | **1.00x** | 552 (40.9%) |
| EPA-HQ-OAR-2021-0317 | EPA | 3,449 | **242.48x** | 115 (3.3%) |
| EPA-HQ-OAR-2013-0602 | EPA | 18,406 | **236.67x** | 438 (2.4%) |

regulations.gov publishes a `duplicateComments` field. **Both EPA dockets use it, eight
years apart, at ~240x. The other four agencies do not use it at all** -- three report the
submission count as exactly equal to the record count -- while holding between 41% and 92%
byte-identical duplicates.

It is not era: EPA-2021 and FDA-2021 are the same year at opposite extremes. It is not
size: OSHA at 1,351 records and ED at 238,659 behave identically. It is not salience: Title
IX and the menthol ban are among the most contested rules in the set and both report 1.00x.

**It is an agency-level convention, and nothing on the page tells a reader which kind of
number they are looking at.** Comparing comment volumes across agencies -- which is what
press coverage and litigation do -- compares two different measurements.

Largest single case: one Fish & Wildlife cluster is **27,807 byte-identical letters**,
published as 27,807 comments, human-confirmed as a campaign.

## And the agency's response does not scale with either count

| docket | submissions | distinct arguments | response passages | per argument |
|---|---|---|---|---|
| EPA-HQ-OAR-2013-0602 | 4,356,240 | 15,845 | 157 | **0.0099** |
| EPA-HQ-OAR-2021-0317 | 836,313 | 3,060 | 313 | 0.1023 |
| ED-2021-OCR-0166 | 238,659 | 83,675 | 1,716 | 0.0205 |
| FWS-HQ-ES-2018-0006 | 65,758 | 2,885 | 109 | 0.0378 |
| OSHA-2010-0034 | 1,351 | 597 | 198 | **0.3317** |

OSHA received **1,351** submissions and wrote a **605-page** rule. EPA received **4,356,240**
and wrote **303 pages**. Agencies respond to a workload they can absorb; because that
workload is roughly fixed, per-argument engagement falls **33x** as volume rises.

**So a large comment total signals neither more argument nor more attention.**

## Confidence, by claim

| claim | rests on | strength |
|---|---|---|
| 64% of records on four dockets are byte-identical duplicates | SHA-256, no parameters | **unconditional** |
| The official duplicate field is used by EPA and not by four other agencies | a published government field | **unconditional** |
| The largest clusters are campaigns | human labels, 58,251 records, 4/4 campaign | strong |
| ~2,885 distinct arguments on FWS | semantic clustering at a human-constrained threshold | **conditional** -- see below |
| Response effort is flat in volume | a heuristic passage detector over 5 final rules | moderate |

**Where the semantic rung is NOT load-bearing, and why that is deliberate.** Embedding-based
clustering adds 3.1 points over exact matching on FWS (95.49% against 92.37%). Its marginal
merges -- distinct texts pulled into a campaign cluster -- are **not** human-validated. That
number is therefore reported as secondary. The headline rests on exact matching, which has
no threshold to argue about.

## Full method and every correction

`docs/coverage.md`, `docs/phase1.md`, `docs/phase3.md`, `docs/llm_labelling.md`. The reports
include the measurement errors made along the way, because several of them pointed toward
flattering this project's thesis and were caught only by reading the underlying text.
