"""Phase 3: the agency's own response document.

WHERE IT COMES FROM. The mirror carries comment attachments but not document
attachments, so the final rules are not in `s3://mirrulations`. Every rule
record does carry an `frDocNum`, and the Federal Register API serves the full
text keyless and free -- the same shape of move as using the mirror instead of
the rate-limited regulations.gov API.

WHAT A "RESPONSE" IS. A US final rule opens with a preamble that, by long
practice and under the APA's requirement to consider comments, walks through
what commenters said and how the agency answered. That preamble is the response
document. It is not separately published and it is not labelled as such, so it
has to be located inside the rule text.
"""
import json
import os
import re
import urllib.request

FR_API = "https://www.federalregister.gov/api/v1/documents/{}.json"

# Headings a preamble uses to introduce what commenters said. Deliberately
# broad: agencies are not consistent, and missing a section would understate
# how much responding the agency did, which is the direction that would
# flatter this project's thesis.
_RESPONSE_HEAD = re.compile(
    r"^\s*(?:[IVXLC]+\.|[A-Z]\.|\d+\.)?\s*"
    r"(?:(?:Summary\s+of\s+|Public\s+|Response\s+to\s+|Discussion\s+of\s+)?"
    r"Comments?(?:\s+and\s+Responses?)?|Response\s+to\s+Comments?|"
    r"Comment\s+and\s+Response|Public\s+Participation)\s*:?\s*$",
    re.I | re.M)

# Inline markers. Agencies very commonly write "Comment:" / "Response:" pairs,
# or "Commenters stated... EPA agrees...". These are how the responses are
# actually counted.
_COMMENT_MARK = re.compile(r"^\s*Comments?\s*:", re.I | re.M)
_RESPONSE_MARK = re.compile(r"^\s*(?:Agency\s+)?Response\s*:", re.I | re.M)
_COMMENTER = re.compile(r"\b(?:commenters?|some\s+commenters?|many\s+commenters?|"
                        r"several\s+commenters?|one\s+commenter|other\s+commenters?)\b", re.I)


def fr_metadata(fr_doc_num):
    u = FR_API.format(fr_doc_num) + ("?fields[]=title&fields[]=raw_text_url"
                                     "&fields[]=page_length&fields[]=publication_date"
                                     "&fields[]=type&fields[]=html_url")
    return json.loads(urllib.request.urlopen(u, timeout=90).read())


def fetch_text(raw_text_url):
    return urllib.request.urlopen(raw_text_url, timeout=180).read().decode("utf-8", "replace")


def response_stats(text):
    """How much of this rule is the agency answering commenters?"""
    return {
        "chars": len(text),
        "comment_response_pairs": len(_RESPONSE_MARK.findall(text)),
        "comment_markers": len(_COMMENT_MARK.findall(text)),
        "commenter_mentions": len(_COMMENTER.findall(text)),
        "response_headings": len(_RESPONSE_HEAD.findall(text)),
    }


def chunk_preamble(text, words=320, overlap=60):
    """Overlapping word windows, so a response split across a boundary is not
    lost. Overlap matters more here than in the comment corpus: a
    comment-and-response pair runs to several hundred words and a hard split
    would separate the objection from the answer."""
    w = text.split()
    out, i = [], 0
    while i < len(w):
        out.append(" ".join(w[i:i + words]))
        if i + words >= len(w):
            break
        i += words - overlap
    return out


def cache_path(docket, root="data"):
    return os.path.join(root, docket, "final_rule.txt")


def load_or_fetch(docket, fr_doc_num, root="data"):
    p = cache_path(docket, root)
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    meta = fr_metadata(fr_doc_num)
    text = fetch_text(meta["raw_text_url"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


# Counting literal "Response:" headers found 111 pairs in the EPA methane rule
# and ZERO in OSHA's silica rule and EPA's Clean Power Plan. That was a
# detector artifact, not a finding: both write responses in narrative form --
# "OSHA thoroughly reviewed these and did not find them adequate", "In response
# to the concerns of commenters, the final guidelines...". Reporting 0% of
# clusters addressed for those two would have been a fabricated result, and in
# the direction that flatters this project's thesis, which is the direction to
# be most suspicious of.
#
# So a response passage is a window that BOTH refers to commenters AND contains
# the agency doing something about it.
_AGENCY_ACT = re.compile(
    r"\b(?:agree|disagree|agrees|disagrees|declines?|declined|concurs?|"
    r"has\s+revised|have\s+revised|has\s+modified|is\s+finalizing|are\s+finalizing|"
    r"did\s+not\s+find|does\s+not\s+agree|is\s+not\s+persuaded|acknowledges?|"
    r"rejects?|adopted?|has\s+determined|concludes?|considered|reviewed|"
    r"in\s+response\s+to|after\s+considering)\b", re.I)


def response_passages(text, window=700, stride=350):
    """Count windows that reference commenters AND show the agency acting.

    Overlapping windows, so a reference and its response separated by a few
    sentences still land together. Reported as a RATE over the document as well
    as a count, because rule length varies 18x across this corpus.
    """
    n_windows = 0
    n_response = 0
    hits = []
    for i in range(0, max(1, len(text) - window + 1), stride):
        w = text[i:i + window]
        n_windows += 1
        if _COMMENTER.search(w) and _AGENCY_ACT.search(w):
            n_response += 1
            if len(hits) < 5:
                hits.append(i)
    return {"windows": n_windows, "response_windows": n_response,
            "response_density": round(n_response / max(1, n_windows), 4),
            "_offsets": hits}
