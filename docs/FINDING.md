# What does a public comment count measure?

**On four federal dockets, 306,854 of 479,311 comment records are redundant copies of
another record's exact text, and every one is published as a separate comment.**

That sentence uses SHA-256 over whitespace-normalised text. No threshold, no embedding
model, no similarity metric, no human judgement.

## 1. The duplicate counts, and what they actually mean

| docket | agency | records | coverage | `duplicateComments` | submissions | **byte-identical copies** |
|---|---|---|---|---|---|---|
| FWS-HQ-ES-2018-0006 | Fish & Wildlife | 64,019 | 100.0% | populated, **14** records | 65,761 (1.03x) | **59,129 (92.4%)** |
| FDA-2021-N-1349 | FDA | 175,313 | 100.0% | populated, **15** records | 175,504 (1.00x) | **111,350 (63.5%)** |
| ED-2021-OCR-0166 | Education | 238,944 | 100.0% | **0 on every record** | **not published** | **135,823 (56.9%)** |
| OSHA-2010-0034 | OSHA | 1,406 | **74.9%** | **0 on every record** | **not published** | 552 (40.9%) |
| EPA-HQ-OAR-2021-0317 | EPA | 3,578 | 100.0% | populated, 143 records | 837,220 (233.99x) | 115 (3.3%) |
| EPA-HQ-OAR-2013-0602 | EPA | 19,319 | **56.0%** | populated, 341 records | 4,360,986 (225.74x) | 438 (2.4%) |

**`duplicateComments` is not a deduplication pass. It is a count of letters inside a bundled
attachment.** On all four dockets that populate it, **100% of records with a value above 1
carry an attachment**, and their comment bodies are 12 to 50 characters -- "See attached".
The project verifies this independently: counting how many times a bundled PDF repeats its own
opening paragraph reproduces the published field exactly, 61,999 and 41,434, with no metadata.

So the 226x gap is **not** an agency policy about deduplication. It is a fact about **how a
campaign was filed**:

> An advocacy group that collects 27,807 signatures and files them as **one PDF** produces
> **one record** with `duplicateComments = 27,807`. A group that routes the same 27,807
> people through a web form produces **27,807 records**, each counted as one comment.
>
> **Both are accurate. They differ by four orders of magnitude. Nothing on the page says
> which you are reading.**

FWS is the clean demonstration: **27,807 byte-identical letters, filed individually,
published as 27,807 comments**, human-confirmed as a campaign. Had that campaign used a
bundle, the docket would read 1.

**And on two dockets the field is not populated at all.** ED and OSHA carry `0` on every
record, so no submission count is published and a reader cannot tell whether duplication was
measured and found absent or never measured.

## 2. How much does the headline move under different choices?

The one unstated choice is *which text represents a comment* (body, or the attachment it
points to). Recomputed under six alternatives:

| variant | redundant copies | vs published |
|---|---|---|
| **published** (assembled text, NFKC + lower + whitespace) | **306,854** | baseline |
| no lowercasing | 306,675 | −0.06% |
| no NFKC | 306,854 | 0 |
| no whitespace collapse | 306,854 | 0 |
| no envelope/receipt stripping | 306,848 | −0.002% |
| strip punctuation too | 307,511 | +0.21% |
| raw comment body instead of assembled text | 311,658 | +1.57% |

**Range 306,675 to 311,658. "64% of records" holds under every variant.** NFKC and whitespace
collapse are no-ops because `assemble.normalize_space` already applied both upstream.

The duplicates are not trivially short text: excess copies are ≥200 characters for 99.9% of
FWS, 99.6% of FDA, 95.4% of ED and 99.0% of OSHA. The largest clusters are 700 to 2,100 character
form letters. "Many people independently typed *I oppose this*" is not the explanation.

## 3. Agency response does not scale with volume (weakly evidenced)

| docket | submissions | distinct arguments | response windows | per argument | response **density** |
|---|---|---|---|---|---|
| EPA-HQ-OAR-2013-0602 | 4,360,986 | 15,845 | 157 | 0.0099 | 0.022 |
| EPA-HQ-OAR-2021-0317 | 837,220 | 3,060 | 313 | 0.1023 | 0.035 |
| ED-2021-OCR-0166 | not published | 83,675 | 1,716 | 0.0205 | **0.185** |
| FWS-HQ-ES-2018-0006 | 65,761 | 2,885 | 109 | 0.0378 | 0.148 |
| OSHA-2010-0034 | not published | 597 | 198 | 0.3317 | 0.021 |

OSHA received 1,406 records and wrote a **605-page** rule; EPA received 4.36M submissions and
wrote **303 pages**. But this claim is **weak and is labelled as such**:

- n=5, and `spearman(submissions, response windows) = 0.10, p = 0.87`. The "flat" claim is
  indistinguishable from noise.
- **The ordering reverses under a different measure.** By response *density* OSHA is
  second-lowest of the five and ED is highest; OSHA tops the per-argument column only because
  it has 597 distinct arguments.
- The denominator is the semantic rung, which this project labels conditional.
- FDA is excluded: its rule was never finalised, so there is no response document at all.

## 4. Confidence, by claim

| claim | rests on | strength |
|---|---|---|
| 306,854 redundant copies, 64% of records | SHA-256; stable to ±1.6% across six variants | **near-unconditional** |
| `duplicateComments` counts bundled-attachment letters | 100% of >1 records have an attachment; independent recount matches exactly | **strong** |
| Published counts depend on filing mode, not on deduplication policy | the above, on 6 dockets / 5 agencies | **strong** |
| ED and OSHA do not publish a submission count | the raw field is 0 on every record | **unconditional** |
| The largest FWS clusters are campaigns | 4 clusters, **12 documents actually read**, one labeller (the author), one docket | **moderate** |
| ~2,885 distinct arguments on FWS | semantic clustering at a human-constrained threshold; moves 5.25% to 23.22% on one label flip | **conditional** |
| Response effort is flat in volume | heuristic detector, n=5, p=0.87, reverses under another measure | **weak** |

## 5. What this does not do

Measures distinctness, not authenticity. A deduplicated count counts arguments, not people.
Organised participation is participation. Six dockets chosen, not sampled. Two are partial
(OSHA 74.9%, EPA-2013 56.0%) and their absolute counts are not the dockets'.

Method, and every correction made along the way, in `docs/coverage.md`, `docs/phase1.md`,
`docs/phase3.md`, `docs/llm_labelling.md`. Several of those errors pointed toward flattering
this project's own thesis and were caught only by reading the underlying text.
