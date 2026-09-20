# How to label a pair

## The question

**Did two people each make this argument, or did one organisation make it and two
people send it?**

Not whether they agree. Not whether they are right. Not whether the writing is
good. Only whether the *argument* is one thing or two.

## The tell

Shared distinctive phrasing, not shared opinion.

Two strangers can independently write "this rule should be stronger" and mean it
independently. That is ordinary agreement. But a shared unusual sentence, a
shared list in the same order, or a shared statistic phrased the same way means
one text was supplied to both.

## The labels

| key | label | means |
|---|---|---|
| `s` | same | one argument, sent twice. Different signature, town, or a line of personal context does not change that. |
| `v` | variant | from a common source, but one adds a real substantive point: a new objection, new evidence, a different remedy. |
| `d` | distinct | each wrote their own, even if they reach the same conclusion. |
| `u` | unusable | too garbled or truncated to judge. |

## Worked examples

All from EPA-HQ-OAR-2021-0317, none of them in the 25-pair sample.

**cosine 1.000 -> `same`.** Byte-identical including the same signatory. One
submission filed twice.

**cosine 0.931 -> `same`.** Openers differ ("As a highly concerned U.S.
citizen..." against "Thank you for taking action..."), then both run "big step in
the right direction... strengthen the final rules to maximize emissions
reductions... the climate crisis is...". Nobody independently produces that
chain. The personal opener is a fill-in-the-blank on supplied text.

**cosine 0.876 -> still `same`.** Much more heavily reworded, same skeleton
underneath. Heavy rewording is what modern campaign tooling does, which is the
reason this project exists at all.

**cosine 0.919 -> `variant`.** Both carry the same three-point template (limit
flaring / storage tank standards / Super Emitter Response Program), but one adds
"per independent scientist", "and check regularly", and extends the scope to
"pipelines, compressor stations, drilling, abandoned wells, leaking 'plugged'
wells". A real addition on top of supplied text.

## The tie-break, and why it is not arbitrary

**Torn between `same` and `distinct`? Choose `distinct`.**

Merging two genuinely separate arguments erases a member of the public from the
record. Splitting one campaign into two merely overstates diversity. The first is
worse. That asymmetry was declared before any numbers existed and it is what the
operating point is selected against, so honouring it here is what makes the
declaration meaningful rather than decorative.

## What these labels decide

The similarity threshold at which the pipeline stops merging. That threshold sets
the reported collapse on this docket, on the OSHA control, and on the five dockets
in Phase 2. Right now it rests on labels a model wrote about its own output, which
is the weakest joint in the whole result.

Do not read `machine_labels.json` first. The entire value is independence; after
both exist, `src/agreement.py` reports Cohen's kappa between them.
