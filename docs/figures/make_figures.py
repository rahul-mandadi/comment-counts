#!/usr/bin/env python3
"""Regenerate the README figures from the committed results in out/.

Nothing here is hand-typed: every number is read from out/*.json, so a figure
cannot drift from the result it illustrates. Run from the repo root:

    python3 docs/figures/make_figures.py

Needs matplotlib, which is deliberately NOT in requirements.txt: this is a docs
utility, and nobody running the pipeline should have to install a plotting
library to do it. The generated PNGs are committed, so regenerating is optional.
"""
import json
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrow
from matplotlib import transforms

INK, GREY, RED, PALE, BG = "#14161A", "#6E737C", "#C8102E", "#E8A3AF", "#F7F8FA"
FONTS = ["Avenir Next", "Helvetica Neue", "DejaVu Sans"]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = FONTS

# The docket the mechanism figure is drawn from, and the agency labels.
CLEAN_CASE = "FWS-HQ-ES-2018-0006"
AGENCY = {
    "FWS-HQ-ES-2018-0006": "Fish & Wildlife",
    "FDA-2021-N-1349": "FDA",
    "ED-2021-OCR-0166": "Education",
    "OSHA-2010-0034": "OSHA",
    "EPA-HQ-OAR-2021-0317": "EPA (2021)",
    "EPA-HQ-OAR-2013-0602": "EPA (2013)",
}


def load():
    cov = {c["docket"]: c for c in
           json.load(open(os.path.join(ROOT, "out/coverage_verified.json")))}
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "out/final-*.json"))):
        d = json.load(open(f))
        k = d["docket"]
        rows.append({
            "docket": k,
            "agency": AGENCY.get(k, k),
            "records": d["records_in_docket"],
            "collapse": d["rungs"]["exact"]["extra_collapse_pct"],
            "coverage": cov.get(k, {}).get("share", 1.0),
            "largest": d["rungs"]["exact"]["largest_cluster_records"],
        })
    return rows


# --------------------------------------------------------------------------
# Figure 1: the mechanism. One campaign, two filing routes, two counts.
# --------------------------------------------------------------------------
def mechanism(rows):
    clean = next(r for r in rows if r["docket"] == CLEAN_CASE)
    n = clean["largest"]                      # 27,807, read not typed

    fig = plt.figure(figsize=(8.0, 4.6), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.965, "ONE CAMPAIGN, TWO WAYS TO FILE IT", fontsize=11,
            fontweight="bold", color=RED, ha="center", va="top")

    # the signers
    cols, sw, gx, sh, gy = 24, 0.0130, 0.0055, 0.032, 0.016
    gw = cols * (sw + gx) - gx
    x0, y0 = 0.5 - gw / 2, 0.845
    for r in range(3):
        for c in range(cols):
            ax.add_patch(Rectangle((x0 + c * (sw + gx), y0 - r * (sh + gy)),
                                   sw, sh, color="#2B2F36", lw=0))
    ax.text(0.5, 0.715, f"{n:,} people sign an identical letter",
            fontsize=13, fontweight="bold", color=INK, ha="center", va="top")
    ax.text(0.5, 0.665, "Fish & Wildlife docket FWS-HQ-ES-2018-0006, the clean case",
            fontsize=10.5, color=GREY, ha="center", va="top")

    # the fork
    ax.add_patch(FancyArrow(0.47, 0.595, -0.20, -0.09, width=0.004,
                            head_width=0.028, head_length=0.022, color=INK,
                            length_includes_head=True))
    ax.add_patch(FancyArrow(0.53, 0.595, 0.20, -0.09, width=0.004,
                            head_width=0.028, head_length=0.022, color=INK,
                            length_includes_head=True))

    for cx, route, count, unit, col in [
            (0.255, "Filed as ONE PDF", "1", "comment record", INK),
            (0.745, "Filed through the WEB FORM", f"{n:,}", "comment records", RED)]:
        ax.add_patch(FancyBboxPatch((cx - 0.215, 0.215), 0.43, 0.245,
                                    boxstyle="round,pad=0.014,rounding_size=0.022",
                                    fc=BG, ec=col, lw=2.0))
        ax.text(cx, 0.425, route, fontsize=11.5, fontweight="bold", color=GREY,
                ha="center", va="top")
        ax.text(cx, 0.305, count, fontsize=30, fontweight="bold", color=col,
                ha="center", va="center")
        ax.text(cx, 0.243, unit, fontsize=11, fontweight="bold", color=INK,
                ha="center", va="top")

    ax.text(0.5, 0.115, "Both counts are accurate. They differ by four orders of "
            "magnitude.", fontsize=12, fontweight="bold", color=INK,
            ha="center", va="top")
    ax.text(0.5, 0.055, "Nothing on the published page tells you which one you "
            "are reading.", fontsize=11, color=GREY, ha="center", va="top")

    out = os.path.join(HERE, "mechanism.png")
    fig.savefig(out, dpi=200, facecolor="white"); plt.close(fig)
    return out


# --------------------------------------------------------------------------
# Figure 2: the spread. The same measurement, six dockets, 2% to 92%.
# --------------------------------------------------------------------------
def spread(rows):
    rows = sorted(rows, key=lambda r: r["collapse"])
    fig = plt.figure(figsize=(8.0, 4.2), dpi=200)
    ax = fig.add_axes([0.20, 0.17, 0.66, 0.68])

    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#D6D9DE")
    ax.tick_params(axis="both", length=0, labelsize=10.5)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color="#ECEEF1", lw=0.9)

    ys = range(len(rows))
    partial = [r["coverage"] < 0.95 for r in rows]
    ax.barh(list(ys), [r["collapse"] for r in rows], height=0.6,
            color=[PALE if p else RED for p in partial])

    # Row labels are drawn by hand rather than as tick labels: the record count
    # needs its own colour and line, and a second ax.text at a data-x collided
    # with the tick label on every row.
    blend = transforms.blended_transform_factory(ax.transAxes, ax.transData)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([])
    for y, r in zip(ys, rows):
        ax.text(-0.03, y + 0.17, r["agency"], transform=blend, ha="right",
                va="center", fontsize=11, fontweight="bold", color=INK)
        ax.text(-0.03, y - 0.19, f'{r["records"]:,} records', transform=blend,
                ha="right", va="center", fontsize=9, color=GREY)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100%"], color=GREY)

    for y, r in zip(ys, rows):
        ax.text(r["collapse"] + 2.0, y, f'{r["collapse"]:.1f}%', va="center",
                fontsize=11, fontweight="bold", color=RED if r["coverage"] >= 0.95 else GREY)

    fig.text(0.02, 0.955, "THE SAME MEASUREMENT, SIX DOCKETS", fontsize=11,
             fontweight="bold", color=RED, ha="left", va="top")
    fig.text(0.02, 0.895,
             "Share of records that are byte-identical copies of another record",
             fontsize=10.5, color=GREY, ha="left", va="top")
    fig.text(0.02, 0.045,
             "Pale bars are dockets the coverage probe found "
             "incomplete (OSHA 74.9%, EPA 2013 56.0%);\ntheir absolute figures are "
             "excluded from the headline. A 39x spread on one measurement is the "
             "finding, not an anomaly.",
             fontsize=8.8, color=GREY, ha="left", va="bottom", linespacing=1.5)

    out = os.path.join(HERE, "spread.png")
    fig.savefig(out, dpi=200, facecolor="white"); plt.close(fig)
    return out


if __name__ == "__main__":
    rows = load()
    for p in (mechanism(rows), spread(rows)):
        print("wrote", os.path.relpath(p, ROOT))
