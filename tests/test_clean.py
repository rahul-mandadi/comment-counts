import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import clean


REAL = ("From: susiesart56@everyactioncustom.com <susiesart56@everyactioncustom.com> "
        "To: A-AND-R-DOCKET Date: 1/9/2023 6:39:06 PM Subject: Comments re: "
        "Docket ID No. EPA-HQ-OAR-2021-0317 ---------- Dear Environmental Protection "
        "Agency, Thank you for taking action to reduce methane emissions.")


def test_envelope_is_detected_on_a_real_record():
    assert clean.has_envelope(REAL)


def test_cleaning_keeps_the_argument_and_drops_the_envelope():
    out = clean.clean(REAL)
    assert out.startswith("Dear Environmental Protection Agency,")
    assert "Thank you for taking action" in out
    assert "everyactioncustom" not in out and "A-AND-R-DOCKET" not in out


def test_a_comment_with_no_envelope_is_untouched_except_whitespace():
    body = "I oppose this rule because methane leaks harm my community."
    assert clean.clean(body) == body


def test_no_salutation_means_nothing_is_guessed_at():
    # envelope present but no salutation: leave it alone rather than cut blind
    t = "From: a@b.com To: x Subject: y Date: z Methane rules should be stronger."
    out = clean.clean(t)
    assert "Methane rules should be stronger." in out
    assert out.startswith("From:")


def test_a_quoted_email_in_the_MIDDLE_is_not_removed():
    t = ("Dear Administrator, our position follows. We previously wrote: "
         "From: staff Sent: Monday Subject: prior comment. That still stands.")
    out = clean.clean(t)
    assert "That still stands." in out and "We previously wrote" in out


def test_docket_boilerplate_goes_because_every_comment_shares_it():
    assert "EPA-HQ-OAR-2021-0317" not in clean.clean(
        "Docket ID No. EPA-HQ-OAR-2021-0317 I support the rule.")
