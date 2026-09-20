# Phase 1: one docket, end to end

Docket **EPA-HQ-OAR-2021-0317** (EPA, methane standards for new and existing oil and gas
sources). Run 2026-09-20. Code in `src/`, 45 tests, labels in `labels/`.

**Why this docket and not the pilot.** The coverage check found EPA-HQ-OAR-2013-0602 holds
roughly 56% of its records. Running the headline on a docket known to be partial would have
baked that defect into the result. EPA-HQ-OAR-2021-0317 has **zero numbering holes**, a 79.3%
attachment rate, and 3,578 records, so it is clean, content-rich and small enough to run
whole. It is also an EPA sibling of the pilot, so the within-agency pair the selection wanted
is preserved.

## The corpus

| | |
|---|---|
| comment records (distinct, post `keys.py`) | 3,578 |
| submissions they represent (sum of `duplicateComments`) | **836,351** |
| **submissions per record** | **233.99** |
| records with `duplicateComments` > 1 | 143 (4.0%) |
| text taken from the comment body | 1,141 |
| text taken from attachments | 2,346 |
| **no usable text at all** (reported, not dropped) | **91 (2.5%)** |
| usable records analysed | 3,487 |

**The pilot's headline replicates on a docket coverage cleared.** Phase 0 measured 225.7
submissions per record on EPA-HQ-OAR-2013-0602. Here it is **233.99**, independently, on a
different rule in a different year with no missing records. The two-counts finding does not
rest on the partial docket.

## Two data defects found on the way, one of which reversed my own prediction

**1. "See attached file(s)" — 263 records.** The placeholder detector was written from
imagination first, then checked against the corpus's most frequent short bodies. It missed
the docket's **second most common body**, 263 records, because the regex had no `(s)`. Also
missed `please post attached comment` and `Please see the uploaded document`. Pinned by
tests that quote the corpus verbatim.

**2. Email envelopes in a third of the extracted text.** 1,136 of 3,487 records (32.6%) begin
with the transport envelope: sender address, timestamp, the `A-AND-R-DOCKET` mailbox, the
scanning clerk's name, attachment filenames. pdfminer extracts it because it is on the page.

I predicted, in the module's own docstring, that shared boilerplate would inflate similarity
and therefore inflate the collapse. **That was wrong, and the measurement is the interesting
part.** Stripping the envelope moved semantic collapse from 25.09% to **27.79%** — it went
*up*. The envelope is not mostly shared: per record it carries a unique email address, a
unique timestamp and a unique name, and that noise was pushing genuinely identical campaign
letters apart. The contamination was **suppressing** the measured collapse, not inflating it.

## The clustering choice that decides everything

Connected components over a similarity graph is **single linkage**: one edge merges. On the
semantic rung it chains badly. Measured at cosine 0.90, the largest component holds 944
records and has **diameter 14** — a path of fourteen hops, so the documents at its ends are
not similar to each other at all. At 0.85 it swallows 1,781 records and 655,866 submissions,
**78% of the docket**. Reporting that as one campaign would have been a fabricated finding
that looked spectacular.

Complete linkage requires *every* pair in a cluster to clear the threshold, so a chain cannot
form. It is also the conservative direction for the asymmetry declared before any labelling:
**merging two genuinely distinct arguments erases a member of the public from the record;
splitting one campaign in two merely overstates diversity.** The first is worse.

| semantic @0.90 | clusters | largest cluster | its submissions |
|---|---|---|---|
| single linkage (connected components) | 2,126 | 944 | 473,682 |
| **complete linkage** | **2,518** | **35** | 166,577 |

## Pair labels

140 pairs, stratified over seven similarity bands so the labels are informative near the
threshold rather than piled on obvious cases. **100 were read individually** (every band from
0.80 up); the two bottom bands were not, and 8 random spot-checks from them were all
`distinct`, so they are recorded as **unlabelled rather than as negatives**.

Distribution: 48 `same`, 47 `distinct`, 4 `variant`, 1 `unusable`.

> **These are machine labels.** They were produced by the assistant, not by a human. The spec
> requires judge-human agreement to be measured before judge output enters a finding, so
> **every precision and recall number below is provisional** until a human labels a subset.
> `labels/for_human.jsonl` holds 25 pairs, 5 per band, for exactly that.

| rung | precision | recall | F1 | tp | fp | fn | tn |
|---|---|---|---|---|---|---|---|
| exact hash | **1.000** | 0.229 | 0.373 | 11 | 0 | 37 | 51 |
| near, MinHash @0.5 | 0.917 | 0.458 | 0.611 | 22 | 2 | 26 | 49 |
| near, MinHash @0.7 | **1.000** | 0.438 | 0.609 | 21 | 0 | 27 | 51 |
| semantic @0.85 | 0.608 | **1.000** | 0.756 | 48 | 31 | 0 | 20 |
| semantic @0.90 | 0.763 | 0.938 | **0.841** | 45 | 14 | 3 | 37 |
| semantic @0.95 | 0.900 | 0.750 | 0.818 | 36 | 4 | 12 | 47 |
| semantic @0.97 | **1.000** | 0.479 | 0.648 | 23 | 0 | 25 | 51 |

The sample is stratified over *semantic* similarity, so exact and near are being judged on a
sample drawn by a different rung's ranking. Use this to pick an operating point; do not quote
it as the precision of MinHash on federal dockets generally.

## The result

Operating points chosen for **precision**, as declared in advance, and clustered with
**complete linkage on both rungs** so the comparison is like for like.

| rung | clusters | extra collapse | cost |
|---|---|---|---|
| exact hash (P=1.00) | 3,398 | 2.55% | seconds |
| **near, MinHash @0.70 (P=1.00)** | **3,195** | **8.37%** | ~30s CPU, no model |
| **semantic @0.97 (P=1.00)** | **3,169** | **9.12%** | model download + ~45s encode |

**At matched precision the expensive rung buys 0.75 percentage points.** 26 clusters out of
3,487. Embeddings, a downloaded model and an encoding pass beat forty lines of MinHash by an
amount that would not survive a different random seed.

Stated against the kill condition as it was actually written — *"semantic collapses by
approximately the same fraction as exact-string dedup"* — it does **not** fire: 9.12% against
2.55% is 3.6x, so embeddings comfortably beat exact hashing. It is the rung **immediately
below** that they fail to beat. The honest sentence is: *character-level near-duplicate
detection captures essentially everything semantic embeddings capture at equal precision on
this docket, and exact hashing captures about a quarter of it.*

### The margin over the official count, which is the number that matters

| | |
|---|---|
| submissions | 836,351 |
| records (what regulations.gov shows) | 3,487 |
| clusters (precision-selected) | 3,169 |
| **collapse the government already did** | **239.85x** |
| **collapse this project adds** | **1.10x** |
| total | 263.92x |
| **share of the whole reduction already official** | **99.96%** |

At the F1-optimal point (semantic 0.90, precision 0.76) the project's own collapse rises to
1.38x. It is still under 1% of the total.

**So the deduplication is not the finding, and the spec said so before any of this ran.**
regulations.gov already publishes `duplicateComments`, and it already bundles the campaigns.
What is left after it is very nearly all distinct.

**The finding is the thing that was true before a single cluster was computed:** this docket
has two official counts, **836,351 and 3,578**, they differ by 234x, both are correct, both
are published, and nothing on the page says which one a reader is looking at.

## What this does not establish

- It does not determine whether any comment is fraudulent. Distinctness is not authenticity.
- It does not measure public opinion. A deduplicated count counts arguments, not people.
- It does not establish that campaign comments are less legitimate. Organised participation is
  participation.
- **One docket.** The 233.99x replicates the pilot's 225.7x, which is two EPA dockets, not a
  population.
- **91 records (2.5%) have no usable text** and are excluded from clustering while remaining
  in every count. They are not a random sample: scanned and paper submissions skew toward
  organised campaigns.
- **The labels are machine labels.** Nothing here has been checked by a human.

## Next

1. Human labels on `labels/for_human.jsonl`, then judge-human agreement. Until that exists,
   the precision column is an assertion.
2. Phase 2, the remaining dockets, for a cross-docket spread. The control docket
   (OSHA-2010-0034) is what tests whether this measures coordination or just writing similarity.
3. Phase 3, the response arm. Cut first if anything slips.
