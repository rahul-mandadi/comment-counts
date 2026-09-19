import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import keys


def test_plain_key():
    assert keys.comment_id("a/b/OSHA-2010-0034-1744.json") == "OSHA-2010-0034-1744"


def test_suffixed_key_collapses_to_same_id():
    plain = "p/FDA-2021-N-1349-53031.json"
    dup = "p/FDA-2021-N-1349-53031(1).json"
    assert keys.comment_id(dup) == keys.comment_id(plain) == "FDA-2021-N-1349-53031"


def test_suffixed_copy_wins_because_it_is_the_later_refetch():
    plain = "p/FDA-2021-N-1349-53031.json"
    dup = "p/FDA-2021-N-1349-53031(1).json"
    assert keys.dedupe([plain, dup]) == {"FDA-2021-N-1349-53031": dup}
    assert keys.dedupe([dup, plain]) == {"FDA-2021-N-1349-53031": dup}


def test_dedupe_counts_records_not_objects():
    ks = ["p/X-2021-N-1-1.json", "p/X-2021-N-1-1(1).json", "p/X-2021-N-1-2.json"]
    assert len(ks) == 3 and len(keys.dedupe(ks)) == 2


def test_a_paren_inside_a_real_id_is_not_a_copy_suffix():
    # only a trailing (digits) marks a copy; nothing else may be stripped
    assert keys.comment_id("p/ED-2021-OCR-0166-1(a).json") == "ED-2021-OCR-0166-1(a)"


def test_sequence_number():
    assert keys.sequence_number("EPA-HQ-OAR-2013-0602-0621") == 621
    assert keys.sequence_number("EPA-HQ-OAR-2013-0602") == 602  # documented sharp edge
