import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import assemble


def test_see_attached_is_a_placeholder_not_a_comment():
    for body in ["See attached", "see attached.", "Please see the attached file",
                 "SEE ATTACHMENT", "Attachments", "N/A", ""]:
        assert assemble.is_placeholder(body), body


def test_a_short_real_opinion_is_NOT_a_placeholder():
    # dropping these would erase members of the public from the record
    for body in ["I oppose this rule.", "No.", "Please do not weaken these standards."]:
        assert not assemble.is_placeholder(body), body


def test_a_body_that_merely_mentions_an_attachment_is_kept():
    body = ("Our organization opposes the proposed standard. See attached for our "
            "full technical analysis of the leak detection frequency.")
    assert not assemble.is_placeholder(body)
    text, src = assemble.assemble({"comment": body}, ["long attachment text"])
    assert src == "body" and text == assemble.normalize_space(body)


def test_placeholder_body_falls_through_to_the_attachment():
    text, src = assemble.assemble({"comment": "See attached"}, ["The real argument."])
    assert src == "attachment" and text == "The real argument."


def test_no_body_and_no_attachment_is_reported_not_dropped():
    text, src = assemble.assemble({"comment": "See attached"}, [])
    assert src == "none" and text == ""


def test_html_is_stripped_before_the_placeholder_test():
    text, src = assemble.assemble({"comment": "<p>See attached</p>"}, ["real text"])
    assert src == "attachment"


def test_whitespace_normalisation_is_not_content_change():
    assert assemble.normalize_space("a  b\n\nc") == "a b c"


# The cases below are verbatim from EPA-HQ-OAR-2021-0317. Every one of them was
# a MISS in the first draft of the regex, found by checking the regex against
# the corpus's most common short bodies instead of against imagination.
def test_real_corpus_placeholders():
    seen_in_corpus = [
        ("See attached file(s)", 263),   # second most common body on the docket
        ("Please see the uploaded document.", 2),
        ("please post attached comment.", 1),
        ("Please see attached comment letter.", 2),
    ]
    for body, _n in seen_in_corpus:
        assert assemble.is_placeholder(body), body


def test_real_corpus_non_placeholders():
    for body in ["I am opposed to these new standards",
                 "We have to get these stupid bastards out of Washington.",
                 "Comment submitted by Alaska Oil and Gas Association",
                 "Useless legislation"]:
        assert not assemble.is_placeholder(body), body


def test_a_quoted_placeholder_is_still_a_placeholder():
    # six records on OSHA-2010-0034 have exactly this body, quote marks included
    for body in ['"See attached"', '"see attached."', "'See attached'",
                 '“See attached”']:
        assert assemble.is_placeholder(body), body


def test_quotes_around_real_content_do_not_make_it_a_placeholder():
    assert not assemble.is_placeholder('"I oppose this rule and here is why."')
