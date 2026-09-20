# Labels

`machine_labels.json` — 100 pairs labelled by the assistant (claude-opus-5) against the
rubric in `src/pairs.py`. **These are judge labels, not human labels.** Every precision and
recall figure in `docs/phase1.md` derives from them and is provisional.

`for_human.jsonl` — 25 pairs, 5 per similarity band (the five bands at 0.80 and above, which is where every candidate threshold sits), for Rahul to label independently.
Do not read `machine_labels.json` first; the whole value is that the two are independent.
Once filled in, judge-human agreement can be computed and reported *alongside* the finding,
which is what the spec requires and what `monitor-audit` established as the house standard
for anything a model asserts about its own output.

The declared asymmetry, restated because it decides every borderline call: merging two
genuinely distinct arguments erases a member of the public from the record; splitting one
campaign into two merely overstates diversity. **If torn, label `distinct`.**
