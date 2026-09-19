"""Turning mirror object keys into comment IDs, which is not as simple as it looks.

The mirror stores some records twice: `<ID>.json` and `<ID>(1).json`. Measured
2026-09-18 across the six selected dockets, 23,061 objects carry that suffix,
22,999 of them on FDA-2021-N-1349 alone, which is 11.6% of that docket's
objects and makes an object count read **13.1% above** its true record count.

Two facts settle how to handle them, both checked rather than assumed:

1. **No record exists only as a suffixed copy.** Orphan count is 0 on all six
   dockets, so collapsing the suffix never loses a comment.
2. **The copies are not identical.** FDA-2021-N-1349-53031 differs between the
   two: the suffixed copy has `modifyDate` 2023-10-03 against the plain copy's
   2023-02-06, and carries a `category` the plain copy leaves null. The suffixed
   copy is a later re-fetch, so it is the one to prefer.

The reason this is a module rather than a regex inline: counting objects in the
mirror is not counting comments, and the gap is 13% on one of the six dockets.
Any figure computed per-object silently overstates that docket.
"""
import re

_SUFFIX = re.compile(r"^(?P<id>.+?)\((?P<n>\d+)\)$")


def comment_id(key):
    """Canonical comment ID for a `.../<name>.json` mirror key."""
    name = key.rsplit("/", 1)[-1]
    if name.endswith(".json"):
        name = name[: -len(".json")]
    m = _SUFFIX.match(name)
    return m.group("id") if m else name


def copy_rank(key):
    """Higher wins when the same ID appears more than once.

    The suffixed copy is the later re-fetch, so it sorts above the plain one.
    """
    name = key.rsplit("/", 1)[-1]
    if name.endswith(".json"):
        name = name[: -len(".json")]
    m = _SUFFIX.match(name)
    return int(m.group("n")) if m else 0


def dedupe(keys):
    """Map canonical comment ID -> the key to actually read."""
    best = {}
    for k in keys:
        cid = comment_id(k)
        if cid not in best or copy_rank(k) > copy_rank(best[cid]):
            best[cid] = k
    return best


def sequence_number(comment_id_str):
    """Trailing number regulations.gov assigned within the docket, or None."""
    m = re.search(r"-(\d+)$", comment_id_str)
    return int(m.group(1)) if m else None
