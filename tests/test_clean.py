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


# Verbatim shapes from EPA-HQ-OAR-2021-0317. 859 of 3,487 records (24.6%) still
# carried this receipt after the well-formed XML case was handled, because the
# extractor flattens it into a line that no longer parses as XML.
FLAT = ("Page 1 of 1 - 0900006485640465 - Jorge De Cecco - Ukiah CA United States "
        "95482 7074631653 - - <![CDATA[ Dear administrators: You do not have to "
        "cater to industry.")


def test_flattened_fdms_receipt_is_stripped():
    out = clean.clean(FLAT)
    assert out.startswith("Dear administrators:")
    assert "0900006485640465" not in out and "CDATA" not in out
    assert "Ukiah" not in out and "7074631653" not in out


def test_receipt_without_the_page_marker_is_still_stripped():
    t = "09000064855ef831 - Joanna Nix - United States - - <![CDATA[ My name is Joanna."
    assert clean.clean(t) == "My name is Joanna."


def test_a_trailing_cdata_close_goes():
    assert "]]>" not in clean.clean(FLAT + " ]]>")


def test_a_sixteen_hex_string_in_PROSE_does_not_trigger_a_strip():
    # the anchor must be the receipt shape, not any hex-looking token
    t = "Dear EPA, our case number is 0123456789abcdef and we object to the rule."
    assert clean.clean(t) == t


def test_a_normal_comment_is_untouched_by_the_new_rule():
    t = "Dear Administrator Regan, I support the proposed methane standards."
    assert clean.clean(t) == t


def test_render_trailer_is_stripped_from_the_end():
    t = ("We absolutely must pass new regulations to stem methane! ]]> Web "
         "file://prod-rend2k1201/Adlib/DocumentumConnector/Work/7131A2AB-522C-4B8... 4/4/2023")
    out = clean.clean(t)
    assert out == "We absolutely must pass new regulations to stem methane!"


def test_a_record_that_is_ONLY_a_receipt_becomes_empty():
    # 37 records on EPA-HQ-OAR-2021-0317 are nothing but this. Embedding them
    # would put a submission receipt into the corpus as if it were an argument.
    t = ("Page 1 of 1 - 0900006485634d9e - Scott Nelson - Bethel Island CA United "
         "States 94511 - Web file://prod-rend2k1201/Adlib/DocumentumConnector/"
         "Work/6619ECC0-ED1B-4EC... 4/4/2023")
    assert clean.clean(t) == ""


def test_a_receipt_WITH_a_comment_keeps_the_comment():
    t = ("Page 1 of 1 - 0900006485640465 - Jorge De Cecco - Ukiah CA United States "
         "95482 - - <![CDATA[ Dear administrators: do not cater to industry.")
    assert clean.clean(t) == "Dear administrators: do not cater to industry."


def test_the_word_web_in_ordinary_prose_survives():
    t = "Dear EPA, the web of pipelines across our state leaks constantly."
    assert clean.clean(t) == t


def test_salutation_above_the_envelope_values_still_gets_cleaned():
    # pdfminer column order puts "Dear ..." before the sender and date, so the
    # salutation cut alone keeps the envelope. 25 real records looked like this.
    t = ("Perez, JuanB From: Sent: To: Subject: Attachments: Dear Administrator Regan, "
         "Lauren Pollack <lauren@team-arc.com> Friday, January 27, 2023 10:58 AM "
         "A-AND-R-DOCKET Comments for Docket ID No. EPA-HQ-OAR-2021-0317 "
         "Attached you will find names of individuals who commented.")
    out = clean.clean(t)
    assert "A-AND-R-DOCKET" not in out
    assert "Friday, January 27, 2023" not in out
    assert "Attached you will find names of individuals" in out


def test_header_debris_goes_even_with_no_salutation_at_all():
    t = ("From: Sent: To: Subject: A-AND-R-DOCKET Tuesday, February 7, 2023 2:02 PM "
         "Methane emissions must be cut immediately.")
    out = clean.clean(t)
    assert "A-AND-R-DOCKET" not in out
    assert "Methane emissions must be cut immediately." in out


def test_a_date_deep_in_the_body_is_NOT_removed():
    body = ("Dear Administrator Regan, " + "our analysis covers many wells. " * 40 +
            "On Monday, March 3, 2025 the operator reported a release.")
    out = clean.clean(body)
    assert "Monday, March 3, 2025" in out


def test_the_word_to_in_ordinary_prose_is_untouched():
    t = "Dear EPA, we need to act to reduce emissions to protect communities."
    assert clean.clean(t) == t
