"""Decide what text REPRESENTS a comment, which is the load-bearing choice here.

Phase 0 measured that 84.3% of comment bodies on the pilot docket say only
"See attached". So the `comment` field is not the comment, and deduplicating it
would have reported an ~85% collapse that is entirely the phrase "See attached".

The rule, in order:
  1. If the body is substantive, the body IS the comment.
  2. Otherwise, if extracted attachment text exists, that is the comment.
  3. Otherwise the comment has NO usable text. These are counted and reported,
     never silently dropped -- scanned and paper submissions skew toward
     organised campaigns, which is the population being measured.

"Substantive" is deliberately strict about placeholders and nothing else. A
genuinely short comment ("I oppose this rule.") is substantive: it is a real
argument, briefly made, and dropping it would erase a member of the public.
"""
import re
import unicodedata

# Placeholder bodies that stand in for an attachment. Anchored to the WHOLE
# body so a comment that merely mentions an attachment in passing is untouched.
# `(s)` is not decoration: "See attached file(s)" is the SECOND most common body
# on EPA-HQ-OAR-2021-0317 at 263 occurrences, and the first draft of this regex
# missed every one of them.
_NOUN = r"(?:file|document|doc|pdf|letter|comment|attachment|enclosure|submission|"  \
        r"response|below|above|here)(?:\(s\)|s)?"

# A placeholder body stands in for an attachment. Anchored to the WHOLE body,
# so a comment that merely mentions an attachment in passing is untouched.
# Built compositionally rather than as a list of literals, because the real
# corpus spells this a dozen ways and a literal list quietly misses one.
_PLACEHOLDER = re.compile(
    r"^(?:"
    r"(?:please\s+)?(?:kindly\s+)?(?:see|refer\s+to|view|read|post|find)\s+"
    r"(?:the\s+|my\s+|our\s+|attached\s+)*"
    r"(?:attach(?:ed|ment)s?|upload(?:ed)?|enclos(?:ed|ure)s?)?"
    r"(?:\s+" + _NOUN + r")*"
    r"|(?:attach(?:ed|ment)s?|enclos(?:ed|ure)s?|upload(?:ed)?)(?:\s+" + _NOUN + r")*"
    r"|n/?a|none|no\s+comment|test"
    r")"
    r"[\s.,;:!\-]*$",
    re.I,
)


def normalize_space(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))


def is_placeholder(body):
    b = normalize_space(strip_html(body))
    # strip wrapping quotes first: OSHA-2010-0034 files six records whose entire
    # body is the string `"See attached"`, quote marks included, and the first
    # version of this check let every one of them through as real text.
    b = b.strip().strip('"\u201c\u201d\'\u2018\u2019').strip()
    return not b or bool(_PLACEHOLDER.match(b))


# A body can be a POINTER rather than a placeholder: too long and too specific
# for the placeholder regex, but still only signposting the attachment.
#   "See attached comments submitted on behalf of a diverse range of expert
#    stakeholders with experience in and perspective from academia, NGOs..."
# That is 203 characters and says nothing about the rule. 138 records across the
# two dockets worked so far had one, and because the body looked substantive the
# pipeline never opened the attachment -- so it was comparing signposts instead
# of arguments, on exactly the long organisational submissions (GPA Midstream,
# Oklahoma DEQ, Society of the Plastics Industry) where distinctness matters most.
#
# Found by a human labeller marking such a pair `unusable`, which is the whole
# reason the label set has an `unusable` option.
_POINTER = re.compile(
    r"^\s*(?:please\s+)?(?:kindly\s+)?(?:see|refer\s+to|view|read|find)\s+"
    r"(?:the\s+|my\s+|our\s+|a\s+|attached\s+)*"
    r"(?:attach(?:ed|ment)s?|enclos(?:ed|ure)s?|upload(?:ed)?|copy)\b",
    re.I)

# A pointer does not have to OPEN with the verb. Institutions write their own
# name first: "Pima County submits the attached comments...", "Mark Sangil of
# Arktos Environmental hereby submits the attached memorandum...". 31 records
# across the four fetched dockets read that way -- West Virginia DEP, Rutgers,
# Columbia Law School, Minnesota Dept of Health -- and every one had its real
# comment sitting unopened in an attachment while the pipeline compared the
# signpost. Found because a labelled pair turned out to be two such signposts
# differing only in the signatory's name.
_POINTER_MID = re.compile(
    r"\b(?:submits?|submitting|encloses?|enclosing|attaches?|files?|forwards?|"
    r"provides?|offers?|transmits?)\b[^.]{0,80}"
    r"\b(?:attach(?:ed|ment)s?|enclos(?:ed|ure)s?)\b",
    re.I)
POINTER_MID_MAX_CHARS = 600
POINTER_MAX_CHARS = 400


def is_pointer(body):
    """A short body whose whole content is a signpost to an attachment."""
    b = normalize_space(strip_html(body))
    if not b:
        return False
    if len(b) <= POINTER_MAX_CHARS and _POINTER.match(b):
        return True
    # The same thing with the submitter's name in front of the verb. Length
    # alone is too crude a guard: a 400-character comment that makes a real
    # argument and mentions its appendix early would be thrown away. So also
    # require the body to be essentially JUST the signpost -- at most two
    # sentences. A submission that says anything of its own says it in a third.
    if len(b) > POINTER_MID_MAX_CHARS or not _POINTER_MID.search(b[:300]):
        return False
    sentences = [x for x in re.split(r"(?<=[.!?])\s+", b) if x.strip()]
    return len(sentences) <= 2


def assemble(record, attachment_texts):
    """Return (text, source) where source is body | attachment | none."""
    body = normalize_space(strip_html(record.get("comment") or ""))
    joined_avail = normalize_space(" ".join(attachment_texts or []))
    # a pointer defers to the attachment, but ONLY when there is one to defer to
    if body and is_pointer(body) and joined_avail:
        return joined_avail, "attachment"
    if body and not is_placeholder(body):
        return body, "body"
    joined = normalize_space(" ".join(attachment_texts or []))
    if joined:
        return joined, "attachment"
    return "", "none"
