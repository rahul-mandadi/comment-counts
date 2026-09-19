"""The six dockets committed 2026-09-18, before any outcome ratio was computed.

Selection rationale lives in the spec; this file is only the manifest, so the
docket list cannot drift between the coverage check and everything after it.
"""

DOCKETS = [
    # (docket_id, agency_prefix_in_mirror, a-priori salience note)
    ("ED-2021-OCR-0166",    "ED",   "Title IX"),
    ("FDA-2021-N-1349",     "FDA",  "menthol ban"),
    ("FWS-HQ-ES-2018-0006", "FWS",  "Endangered Species Act"),
    ("EPA-HQ-OAR-2013-0602", "EPA", "Clean Power Plan (pilot)"),
    ("EPA-HQ-OAR-2021-0317", "EPA", "methane standards"),
    ("OSHA-2010-0034",      "OSHA", "technical safety rule"),
]

RESERVE = [("FDA-2016-D-2335", "FDA", "held in reserve")]


def comments_prefix(docket_id, agency):
    return f"raw-data/{agency}/{docket_id}/text-{docket_id}/comments/"


def attachments_prefix(docket_id, agency):
    return f"raw-data/{agency}/{docket_id}/binary-{docket_id}/comments_attachments/"


def extracted_prefix(docket_id, agency):
    return (f"derived-data/{agency}/{docket_id}/mirrulations/extracted_txt/"
            f"comments_extracted_text/pdfminer/")
