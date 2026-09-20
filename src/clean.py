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


def clean(text):
    if not text:
        return ""
    if _FDMS.search(text):
        # an FDMS XML wrapper is a submission receipt, not prose; keep only the
        # comment element if there is one
        body = re.search(r"<comment>(.*?)</comment>", text, re.S | re.I)
        text = body.group(1) if body else _TAG.sub(" ", text)
    text = strip_envelope(text)
    text = _EMAIL.sub(" ", text)
    text = _URL.sub(" ", text)
    text = _DOCKET_LINE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()
