# What you are labelling, and why

Written for someone opening this cold.

## The real-world problem

Before a US federal agency issues a rule, it must publish a draft, take public
comments, and consider them. Those comments are public, and **the count becomes
evidence** -- quoted in press coverage, cited in litigation over whether an
agency acted arbitrarily, and used by advocacy groups as a measure of public
sentiment.

Much of that volume is organised. Campaigns supply members with pre-written text
and modern tooling **rewords** it so submissions are not identical. A rule that
reads as 400,000 concerned citizens may be 900 arguments and a mailing list.
That is not illegitimate -- organised participation is participation -- but it is
a different thing, and the record does not distinguish them.

## What this project has established

**1. One rule, two official counts, 242x apart, neither labelled.**
EPA-HQ-OAR-2021-0317 holds 3,449 comment records representing 836,313
submissions. Both correct, both official. Nothing on the page says which one a
reader is looking at.

**2. The government's own duplicate count is excellent -- on some dockets.**
`duplicateComments` is a field regulations.gov publishes. On the EPA docket one
record is a single 206 MB PDF holding thousands of copies of a form letter.
Counting those copies independently by text analysis gives 61,999; the official
field says 61,999. Two unrelated methods, exact agreement.

**3. It does not do that everywhere, and this is the finding.**
On OSHA-2010-0034 every one of 1,351 records carries `duplicateComments = 1`,
while **524 of them are byte-identical copies of one industry form letter**.

> Whether the official record corrects for duplication depends on which docket
> you are reading, and nothing tells you which kind you have. That makes
> cross-docket comparison of comment volumes invalid, which is precisely what
> press and litigation do with these numbers.

## Where the labels come in

Three methods decide whether two comments are "the same", cheapest first:

| method | catches | misses |
|---|---|---|
| exact hash | byte-identical form letters | one changed word |
| MinHash | light edits, inserted names | genuine rewording |
| embeddings | paraphrase, reordering | actually different arguments |

The third produces a similarity score between 0 and 1. A score is not a
decision. Something must say *above this line, call them the same*, and that
line decides everything:

- too loose -> two people who each wrote their own letter get merged, which
  **erases a member of the public from the record**
- too tight -> campaigns are missed and duplication is reported as diversity

Your labels are the ground truth that sets that line and measures how often the
method is wrong.

## Why a human, and why blind

The existing labels were written by the model, judging whether its own
similarity scores were right. That is circular and it is the weakest joint in
the result.

This docket alone has **2,348,271** comparable pairs, so hand-labelling is never
the plan; automation is. These 50 exist to answer one question: **can the model
be trusted to run that automation?** If yes, it labels the rest and you audit a
sample. If no, its labels are dropped, cheaply.

Blind, because a person who sees the model's answer verifies rather than judges,
and afterwards no independent baseline remains to measure the difference.

## Then

    cd ~/dev/comment-counts && .venv/bin/python label_pairs.py
    PYTHONPATH=src .venv/bin/python src/agreement.py

How to apply the four labels, with worked examples: `labels/HOW_TO_LABEL.md`.
