"""Strip transport metadata that is not the comment.

A third of the extracted texts on EPA-HQ-OAR-2021-0317 (1,136 of 3,487) begin
with an email envelope: the agency mailbox that received it, the date, the
scanning clerk's name, the attachment filenames, and the docket ID. pdfminer
faithfully extracts all of it because it is on the page.

That is a problem specific to THIS project rather than a general tidiness
concern. Envelope text is near-identical across an entire campaign -- every
submission routed through the same advocacy platform carries the same
`everyactioncustom.com` sender domain, the same `A-AND-R-DOCKET` recipient and
the same docket line. Embedding it makes two submissions look alike because
they used the same mailing tool, which is precisely the inference the project
is trying to make on the strength of their ARGUMENTS.

The direction of the bias was PREDICTED WRONG here, and the measurement is
recorded because the wrong prediction is the instructive part. The guess was
that shared envelope boilerplate inflates similarity and therefore inflates the
collapse. Measured on EPA-HQ-OAR-2021-0317 at semantic 0.90 with complete
linkage, stripping the envelope moved the collapse from 25.09% to **27.79%** --
it went UP.

The envelope is not mostly shared boilerplate. Per record it carries a unique
sender address, a unique timestamp and a unique name, and that per-record noise
was pushing genuinely identical campaign letters APART. So the contamination
was suppressing the measured collapse rather than inflating it, and the clean
figure is the larger one.

Everything here is conservative. Nothing is removed from the middle of a
document, because a quoted email inside a comment is content.
"""
import re

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_URL = re.compile(r"https?://\S+")
_DOCKET_LINE = re.compile(
    r"\b(?:re:\s*)?Docket\s*(?:ID\s*)?N[oO]\.?\s*:?\s*[A-Z]{2,5}[-–][\w\-]+", re.I)
_HEADER_FIELD = re.compile(r"\b(From|To|Sent|Subject|Date|Cc|Bcc|Attachments?):", re.I)
_SALUTATION = re.compile(
    r"\b(Dear\s+(?:Administrator|Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Sir|Madam|EPA|"
    r"Environmental\s+Protection|Secretary|Director|Sirs?|Madams?|"
    r"[A-Z][a-z]+)[^,\n]{0,60},)")
_FDMS = re.compile(r"<\?xml.*?</fdms_submission>", re.S | re.I)

# The SAME receipt, flattened by the PDF extractor into a single line and with
# its XML tags mostly gone:
#     Page 1 of 1 - 0900006485640465 - Jorge De Cecco - Ukiah CA United States
#     95482 7074631653 - - <![CDATA[ Dear administrators: ...
# 859 of 3,487 records on EPA-HQ-OAR-2021-0317 (24.6%) still carried this after
# the well-formed shape above was handled, because it no longer looks like XML.
# The 16-hex-digit objectId is the reliable anchor: it is the docket system's
# own identifier and does not occur in prose.
_FDMS_FLAT = re.compile(
    r"^\s*(?:Page\s+\d+\s+of\s+\d+\s*[-–]\s*)?"      # optional page marker
    r"[0-9a-f]{16}\b"                                     # the objectId
    r".{0,400}?"                                           # name, city, phone
    r"(?:<!\[CDATA\[|\]\]>)",                             # up to the CDATA opener
    re.S | re.I)
_CDATA_CLOSE = re.compile(r"\]\]>\s*$")

# The rendering system's own trailer, appended after the comment text:
#     ]]> Web file://prod-rend2k1201/Adlib/DocumentumConnector/Work/AD57... 4/4/2023
# 124 records carry it as a SUFFIX, which is why a prefix-only rule left them.
_RENDER_TRAILER = re.compile(
    r"(?:\]\]>\s*)?Web\s+file://\S*(?:Adlib|DocumentumConnector)\S*.*$", re.S | re.I)

# And 37 records are NOTHING BUT the receipt: objectId, name, town, phone, the
# render path, a date. No comment at all. Those must end up empty so the
# pipeline reports them as having no usable text, rather than embedding a
# submission receipt as though it were somebody's argument.
_TAG = re.compile(r"<[^>]{1,80}>")


def has_envelope(text, window=600, min_fields=3):
    return len(set(m.group(1).lower() for m in
                   _HEADER_FIELD.finditer(text[:window]))) >= min_fields


def strip_envelope(text, window=1500):
    """Drop everything before the salutation, but only when BOTH an envelope
    signature and a salutation are present inside the window.

    Requiring both is what keeps it safe. A comment with no salutation is left
    completely untouched rather than guessed at.
    """
    if not text or not has_envelope(text):
        return text
    m = _SALUTATION.search(text[:window])
    if not m:
        return text
    return text[m.start():].strip()


# pdfminer emits a mail header as two column runs: the LABELS first, then the
# VALUES. So a salutation can appear physically above the sender and date:
#   "Perez, JuanB From: Sent: To: Subject: Dear Administrator Regan,
#    Lauren Pollack <...> Friday, January 27, 2023 10:58 AM A-AND-R-DOCKET ..."
# Cutting at "Dear" then KEEPS the envelope values. 25 records came out of the
# first version that way, and 392 more kept their headers because no salutation
# was found at all -- together about 11% of EPA-HQ-OAR-2021-0317. These strip
# the shared boilerplate wherever it sits, without needing to locate the body.
_MAILBOX = re.compile(r"\bA-AND-R-DOCKET\b(?:@\S+)?", re.I)
_LABEL_RUN = re.compile(
    r"(?:\b(?:From|Sent|To|Cc|Bcc|Subject|Attachments?|Importance|Date):\s*){2,}", re.I)
_LONG_DATE = re.compile(
    r"\b(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)?",
    re.I)


def strip_header_debris(text, window=900):
    """Remove mail-header debris from the opening of a document.

    Scoped to a window so a date or a mailbox mentioned in the BODY of a long
    comment survives. Only the opening of a document is envelope.
    """
    if not text:
        return text
    head, tail = text[:window], text[window:]
    head = _LABEL_RUN.sub(" ", head)
    head = _MAILBOX.sub(" ", head)
    head = _LONG_DATE.sub(" ", head)
    return head + tail


def clean(text):
    if not text:
        return ""
    if _FDMS.search(text):
        # an FDMS XML wrapper is a submission receipt, not prose; keep only the
        # comment element if there is one
        body = re.search(r"<comment>(.*?)</comment>", text, re.S | re.I)
        text = body.group(1) if body else _TAG.sub(" ", text)
    m = _FDMS_FLAT.search(text[:600])
    if m:
        text = text[m.end():]
    text = _RENDER_TRAILER.sub(" ", text)
    text = _CDATA_CLOSE.sub(" ", text)
    # a receipt with no CDATA opener leaves the whole header behind; drop it
    m = re.match(r"\s*(?:Page\s+\d+\s+of\s+\d+\s*[-–]\s*)?[0-9a-f]{16}\b.*", text, re.S)
    if m and len(text) < 400:
        text = ""
    text = strip_envelope(text)
    text = strip_header_debris(text)
    text = _EMAIL.sub(" ", text)
    text = _URL.sub(" ", text)
    text = _DOCKET_LINE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()
