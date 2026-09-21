# Phase 3: does the agency respond to the arguments, or to the volume?

Run 2026-09-21. The spec's third arm, and the first result needs no LLM at all.

## Where the response document is

A US final rule opens with a preamble that walks through what commenters said and how the
agency answered. That preamble IS the response document: it is not separately published and
not labelled as such.

The mirror carries comment attachments but **not** document attachments, so the rules are not
in `s3://mirrulations`. Every rule record carries an `frDocNum`, and the **Federal Register
API serves full text keyless and free** -- the same move as using the mirror instead of the
rate-limited regulations.gov API.

| docket | final rule | FR pages | chars |
|---|---|---|---|
| OSHA-2010-0034 | 2016-04800, silica | 605 | 3,287,463 |
| ED-2021-OCR-0166 | 2024-07915, Title IX | 423 | 3,249,058 |
| EPA-HQ-OAR-2021-0317 | 2024-00366, methane | 408 | 3,152,452 |
| EPA-HQ-OAR-2013-0602 | 2015-22842, Clean Power Plan | 303 | 2,543,293 |
| FWS-HQ-ES-2018-0006 | 2019-17518, ESA listing | 34 | 257,766 |
| **FDA-2021-N-1349** | **none** | - | - |

**FDA has no final rule.** The menthol standard drew 175,313 comments and was never
finalised, so there is no agency response to analyse. That is a fact about the docket, not a
gap in the data, and it is the cleanest possible case of comments with no response.

## A measurement error worth keeping

The first counter looked for literal `Response:` headings. It found 111 in the EPA methane
rule, 110 in the FWS rule, and **zero** in OSHA's silica rule and EPA's Clean Power Plan.

Reported as-is that would have read "0.00% of clusters could possibly be addressed" for two
major rules. It is an artifact. Both write responses in narrative form:

> "Some commenters also presented additional studies for OSHA to consider. **OSHA thoroughly
> reviewed these and did not find them adequate** to alter OSHA's overall conclusions..."

> "**In response to the concerns of commenters** that the proposal's 10-year interim target
> failed to afford sufficient flexibility, the final guidelines' approach will provide
> states with realistic options..."

Those are substantive responses. The error was caught by reading the text rather than
trusting the count, and it pointed in the direction that would have **flattered this
project's thesis** -- which is the direction to be most suspicious of.

A response passage is now a 700-character window that both refers to commenters and shows the
agency acting on it (agrees, declines, has revised, did not find, in response to, after
considering). OSHA goes from 0 to 198, EPA-2013 from 0 to 157.

## The result

| docket | submissions | distinct arguments | response passages | **per distinct argument** |
|---|---|---|---|---|
| EPA-HQ-OAR-2013-0602 | 4,356,240 | 15,845 | 157 | **0.0099** |
| EPA-HQ-OAR-2021-0317 | 836,313 | 3,060 | 313 | 0.1023 |
| ED-2021-OCR-0166 | 238,659 | 83,675 | 1,716 | 0.0205 |
| FWS-HQ-ES-2018-0006 | 65,758 | 2,885 | 109 | 0.0378 |
| OSHA-2010-0034 | 1,351 | 597 | 198 | **0.3317** |

**Response effort is roughly constant in absolute terms and unrelated to volume.** Agencies
wrote between 109 and 1,716 response passages whether the docket drew 1,351 submissions or
4.36 million. OSHA received **1,351** submissions and wrote a **605-page** rule; EPA received
**4,356,240** and wrote **303 pages**.

So the answer to the question the spec asked is: **neither.** The agency responds to a
workload it can absorb. Because that workload is roughly fixed, per-argument engagement falls
as volume rises -- **33x** across this corpus, and the docket with 3,200x more submissions
received 33x less response per distinct argument.

This is the complement to the Phase 2 finding. Phase 2 showed the published count does not
measure distinct argument. Phase 3 shows the agency's engagement does not scale with either
count, so a large comment total signals neither more argument nor more attention.

## What is NOT claimed here

- **No per-cluster response matching yet.** "Did the agency respond to THIS campaign" needs
  retrieval plus a judge, and the judge is not validated. `docs/llm_labelling.md` records the
  same model family agreeing with a human at **kappa -0.279** on this corpus's other
  judgement task, so a judge arm here would need its own validation before any output of it
  is reported. Kill condition 4 is live, not cleared.
- **Rule length is not purely response.** A 605-page silica rule contains risk assessment and
  economic analysis alongside the response preamble. The response-passage density measure
  addresses this -- OSHA's is 0.021 against ED's 0.185 -- but page counts alone would not.
- **"Response passage" is a heuristic**, tuned on two conventions found in five rules. It has
  not been validated against human judgement of whether a passage really answers a comment.
