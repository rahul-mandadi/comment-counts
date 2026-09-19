import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import keys


def holes(nums):
    lo, hi = min(nums), max(nums)
    return sorted(set(range(lo, hi + 1)) - set(nums))


def test_attachment_key_maps_to_its_comment():
    k = ("raw-data/OSHA/OSHA-2010-0034/binary-OSHA-2010-0034/"
         "comments_attachments/OSHA-2010-0034-1830_attachment_1.docx")
    assert keys.comment_id(k.rsplit("_attachment", 1)[0] + ".json") == "OSHA-2010-0034-1830"


def test_extracted_text_key_maps_to_the_same_comment():
    k = ("derived-data/OSHA/OSHA-2010-0034/mirrulations/extracted_txt/"
         "comments_extracted_text/pdfminer/OSHA-2010-0034-1830_attachment_1_extracted.txt")
    assert keys.comment_id(k.rsplit("_attachment", 1)[0] + ".json") == "OSHA-2010-0034-1830"


def test_a_comment_with_two_attachments_is_counted_once():
    ks = ["p/X-2010-0034-9_attachment_1.pdf", "p/X-2010-0034-9_attachment_2.pdf"]
    ids = {keys.comment_id(k.rsplit("_attachment", 1)[0] + ".json") for k in ks}
    assert ids == {"X-2010-0034-9"}


def test_holes_are_computed_on_the_union_of_comments_and_documents():
    # regulations.gov numbers documents and comments in ONE sequence. Computing
    # holes from comments alone would report every document slot as missing.
    comments, documents = {2, 4}, {1, 3}
    assert holes(comments | documents) == []
    assert holes(comments) == [3]


def test_dedupe_before_numbering_or_fda_reads_13_percent_high():
    ks = ["p/FDA-2021-N-1349-1.json", "p/FDA-2021-N-1349-1(1).json"]
    assert len(ks) == 2
    assert len(keys.dedupe(ks)) == 1
