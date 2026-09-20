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
    return not b or bool(_PLACEHOLDER.match(b))


def assemble(record, attachment_texts):
    """Return (text, source) where source is body | attachment | none."""
    body = normalize_space(strip_html(record.get("comment") or ""))
    if body and not is_placeholder(body):
        return body, "body"
    joined = normalize_space(" ".join(attachment_texts or []))
    if joined:
        return joined, "attachment"
    return "", "none"
