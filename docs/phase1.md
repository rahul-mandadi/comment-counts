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

Figures below are on the FINAL cleaned text (2026-09-20), after the FDMS
submission-receipt strip described under "A third receipt, and 38 records that
were not comments".

| rung | clusters | extra collapse | cost |
|---|---|---|---|
| exact hash (P=1.00) | 3,334 | 3.33% | seconds |
| **near, MinHash @0.70 (P=1.00)** | **3,099** | **10.15%** | ~30s CPU, no model |
| **semantic @0.97 (P=1.00)** | **3,120** | **9.54%** | model download + ~45s encode |

**At matched precision the expensive rung buys nothing at all.** On the final cleaned text
MinHash reaches 10.15% and embeddings 9.54%, so the cheap rung is now marginally *ahead*. Embeddings, a downloaded model and an encoding pass beat forty lines of MinHash by an
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
| submissions | 836,313 |
| records with usable text | 3,449 |
| clusters (precision-selected) | 3,120 |
| **collapse the government already did** | **242.48x** |
| **collapse this project adds** | **1.11x** |
| total | 268.05x |
| **share of the whole reduction already official** | **99.96%** |

At the F1-optimal point (semantic 0.90, precision 0.76) the project's own collapse rises to
1.38x. It is still under 1% of the total.

**So the deduplication is not the finding, and the spec said so before any of this ran.**
regulations.gov already publishes `duplicateComments`, and it already bundles the campaigns.
What is left after it is very nearly all distinct.

**The finding is the thing that was true before a single cluster was computed:** this docket
has two official counts, **836,351 and 3,578**, they differ by 234x, both are correct, both
are published, and nothing on the page says which one a reader is looking at.

## The incumbent is better than it looks, verified two ways

Three records on this docket are **bundles**: one PDF containing thousands of copies of a
form letter, one per signatory. The largest is **206,968,613 characters** in a single comment
record, which is how a 3,487-record docket produces a mean document length 77x its median.

I counted the copies independently, by finding how many times each document's own opening
paragraph repeats inside itself, with no reference to any metadata:

| record | chars | repeats I counted | official `duplicateComments` |
|---|---|---|---|
| EPA-HQ-OAR-2021-0317-2477 | 206,968,613 | **61,999** | **61,999** |
| EPA-HQ-OAR-2021-0317-2496 | 138,147,331 | **41,434** | **41,434** |
| EPA-HQ-OAR-2021-0317-2469 | 352,200 | 129 | 261 |

**Two of the three agree exactly.** regulations.gov is not estimating; it knows how many
letters are inside a bundled PDF attachment it received as one file. The third differs
because my repeat probe keys on one paragraph and that bundle mixes two letter variants,
which is a limitation of my probe rather than of their count.

This matters because the project's original premise was that bundled campaign submissions
would be invisible to the official count. They are not. It is the sharpest available evidence
that the incumbent is accurate, and it independently reinforces the margin result: there is
very little for a deduplication pipeline to find that the government has not already found.

## A truncation bound that has to be stated

`embed.chunk` caps each document at 24 chunks, roughly 4,300 words. On this docket that means
**2.9% of the corpus text is actually embedded** (10,542,252 characters of 367,168,881).

The cap is doing something reasonable and something questionable at once. Reasonable: the
bundles above are 200 MB of one repeated letter, and embedding all of it would be pure waste.
Questionable: a 30-page industry comment is compared on its opening 4,300 words, so two long
submissions that differ only after page eight are indistinguishable to rung 3.

Since the long documents are overwhelmingly the substantive industry and NGO comments, and the
short ones are the campaign letters this project is trying to separate, **the truncation is
concentrated exactly on the population where distinctness matters most.** It did not affect
the headline, because the collapse is driven by short campaign letters that fit inside the cap
comfortably. It would affect any future claim about the long tail.

## THE CONTROL DOCKET, and it changed the headline

OSHA-2010-0034 (respirable crystalline silica) was chosen a priori as the low-salience
technical control. Its job was to test kill condition 3: *if the control collapses as much as
the campaign-heavy dockets, the method is measuring writing similarity rather than
coordination and the result is retracted.*

**The control collapsed six times harder than the campaign docket.**

| | EPA-HQ-OAR-2021-0317 (salient) | OSHA-2010-0034 (control) |
|---|---|---|
| records | 3,487 | 1,351 |
| **official `duplicateComments`** | **836,351 submissions, 234x** | **1,351 submissions, 1.00x** |
| records the official count flags as duplicated | 143 | **0** |
| exact-hash collapse | 2.55% | **40.86%** |
| semantic @0.97, complete-link | 9.12% | **54.40%** |

**The trigger fired and its inference is false, and the difference matters.** Kill condition 3
presumes that a collapsing control means the method is picking up stylistic similarity. So I
looked at the clusters instead of applying the rule mechanically:

> **524 byte-identical copies of a single industry form letter**, opening *"The Honorable
> David Michaels... As an employer..."*, each 3,776 characters.

Byte-identical text is coordination by definition. An exact hash cannot measure writing style;
it can only find documents that are the same document. So the method is working exactly as
intended, and the control is not a control for what it was meant to control.

### What it actually found

**regulations.gov applied `duplicateComments` on one docket and not at all on the other.**
On the EPA docket the field bundles campaigns so well that independent text analysis
reproduces its counts exactly (61,999 and 41,434, above). On the OSHA docket **every one of
the 1,351 records carries `duplicateComments = 1`**, while 524 of them are the same letter.

So the sentence this project can now defend is stronger than the one it started with:

> **Whether the official record corrects for duplication depends on which docket you are
> reading, and nothing on the page tells you which kind you have.** On one docket the
> published count is accurate to the individual signature inside a bundled PDF. On another,
> 524 identical letters are published as 524 comments.

That makes cross-docket comparison of comment volumes invalid, which is exactly the use those
numbers are put to in press coverage and litigation. It is a measurement-validity finding
rather than a deduplication result, which is what the spec said this project was for.

### Why the margin result still stands, and is better explained

Phase 1 reported that deduplication adds 1.10x against the government's 239.85x on the EPA
docket. That is not because deduplication is weak. **It is because on that docket the work had
already been done.** On a docket where it has not been done, the same ladder finds a 40.86%
exact-duplicate rate that the official count reports as zero.

### Two defects this surfaced

1. **A quoted placeholder.** Six OSHA records have the entire body `"See attached"`, quote
   marks included, and the detector let every one through as real text. Fixed, with the
   corpus strings as the test.
2. **Mojibake splits an exact cluster.** The 524 letters land in groups of 500 and 24 because
   one batch had its curly quotes and en-dashes mangled to `?` by extraction. The two are
   99.47% identical. This is not a bug in the exact rung, which is meant to be brittle -- it
   is a worked demonstration of why the ladder needs a second rung, and the near rung merges
   them correctly.

## A third receipt, and 38 records that were not comments

After the email envelope was stripped, **859 of 3,487 records (24.6%) still opened with a
different receipt** -- the docket system's own render header, flattened by the PDF extractor
until it no longer parsed as XML:

    Page 1 of 1 - 0900006485640465 - Jorge De Cecco - Ukiah CA United States 95482
    7074631653 - - <![CDATA[ Dear administrators: You do not have to cater to industry.

Handling it exposed two more shapes. **124 records** carry the same system's trailer at the
*end* (`]]> Web file://prod-rend2k1201/Adlib/DocumentumConnector/...`), which a prefix rule
cannot reach. And **38 records contain nothing but the receipt** -- objectId, name, town,
phone, render path, date, and no comment at all. Those were being embedded as documents.
They now resolve to empty and are reported as having no usable text, which is what they are.

**Effect on the result: small, and in the direction that matters.**

| | before the fix | after |
|---|---|---|
| exact | 2.55% | **3.33%** |
| near @0.70 | 9.32% | **10.15%** |
| semantic @0.97 | 9.12% | **9.54%** |
| margin over official | 1.10x | 1.11x |

Every conclusion survives, which is the useful part: the headline was not resting on
uncleaned text. **One thing did flip.** Before the fix, embeddings edged MinHash 9.12% to
8.37%. On clean text MinHash reaches 10.15% against embeddings' 9.54%, so at matched
precision **the cheap rung is now ahead**. The 0.75-point advantage previously claimed for
embeddings was an artifact of receipt text that the two rungs handled differently.

Precision and recall on the final text, same 100 machine labels (pair identity is by record
index and survived the text change, so no relabelling was needed):

| rung | precision | recall | F1 |
|---|---|---|---|
| exact | 1.000 | 0.292 | 0.452 |
| near @0.70 | **1.000** | **0.438** | 0.609 |
| semantic @0.90 | 0.804 | 0.938 | **0.865** |
| semantic @0.97 | **1.000** | **0.479** | 0.648 |

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
