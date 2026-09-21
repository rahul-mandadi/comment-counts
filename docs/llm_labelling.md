# Can an LLM do the labelling? Measured, and no.

Hand-labelling does not scale here: EPA-HQ-OAR-2021-0317 alone has 2,348,271 pairs above
cosine 0.60, and there are six dockets. So the plan was always to automate labelling and
validate it. This is the validation, and it failed.

## The design

Three Opus agents labelled the same 40 Jaccard-stratified pairs independently -- blind to each
other, to the earlier machine labels, to the human labels, and to the similarity scores
themselves. Then a human labelled 12 of the same pairs blind. Three labellers rather than one,
so inter-annotator agreement among models could be measured too.

## Result 1: the models agree with each other almost perfectly

| | same | variant | distinct |
|---|---|---|---|
| A | 33 | 6 | 1 |
| B | 30 | 9 | 1 |
| C | 33 | 6 | 1 |

Unanimous on 37/40. **A and C were byte-identical, kappa 1.00.** A/B and B/C kappa 0.778.

**This is not evidence of correctness and must not be reported as though it were.** Three runs
of one model on one prompt is close to one opinion sampled three times, so what it measures is
reproducibility. An agreement statistic computed over labellers that are not independent will
look excellent no matter how wrong they all are.

## Result 2: they disagree with the human worse than chance

Against the 11 usable human labels in the same region:

| labeller | raw agreement | **Cohen's kappa** |
|---|---|---|
| agent A | 0.545 | **-0.279** |
| agent B | 0.545 | -0.038 |
| agent C | 0.545 | **-0.279** |
| majority vote | 0.545 | **-0.279** |

**Kappa below zero is worse than chance** given the marginals. Majority voting did not help,
because the errors are correlated -- which is exactly what result 1 predicts.

The mechanism is visible pair by pair. Ordered by Jaccard:

```
jac 0.336   agents: variant   human: same
jac 0.398   agents: same      human: distinct   <--
jac 0.422   agents: variant   human: same
jac 0.461   agents: same      human: distinct   <--
jac 0.508   agents: same      human: same
jac 0.523   agents: same      human: same
jac 0.578   agents: same      human: same
jac 0.609   agents: same      human: distinct   <--
jac 0.625   agents: same      human: same
jac 0.641   agents: same      human: same
jac 0.797   agents: same      human: same
```

The agents said `same` on 33 of 40 pairs in a sample reaching down to Jaccard 0.30, where two
documents share less than a third of their wording. On **every** pair the human judged to be
two separate arguments, all three agents said one. An earlier measurement on a different sample
had already found this model over-merging 2:1 against the same human; this is that lean, at
scale, in the region where it decides the answer.

## Why it matters beyond this project

The declared asymmetry is that merging two genuinely distinct arguments **erases a member of
the public from the record**, while splitting a campaign merely overstates diversity. An
automated labeller that fails asymmetrically toward merging fails in precisely the direction
that was declared unacceptable before any labelling began.

Had the agent labels been adopted, they would have put the MinHash threshold at **0.8594** --
pinned by a single `distinct` at 0.8359 -- against the human-derived **0.625**. The reported
collapse would have been 7.4% instead of 10.9%.

## What was kept

The agents' 40 labels are **not used** for threshold selection. They are retained in
`labels/agent_*.json` as the evidence for this finding.

Two further things the humans found that no labeller was asked to look for, and that no test
caught:

- a pair whose two texts were both `"See attached comments submitted on behalf of..."` --
  **138 records** whose real comment sat unopened in an attachment
- a pair reading `"<name> of Arktos Environmental hereby submits the attached memorandum"` --
  **31 more**, all institutional submissions

A model answers the question it is asked. A person notices the question is broken. That is a
separate argument for human labelling from the one about label quality, and on this corpus it
was worth more.

## The honest scaling position

Labelling on this corpus does not automate, at least not with this model, this prompt and this
rubric. Phase 2 therefore applies a **frozen** threshold derived from human labels rather than
labelling each docket, and reports the transfer assumption as untested. Where a docket needs
its own operating point, that needs human labels.
