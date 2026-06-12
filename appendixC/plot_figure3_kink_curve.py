import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "result"
DATA = RESULT / "figure3_kink_marginal_effect_notheta_continuous.csv"
PNG = RESULT / "figure3_kink_marginal_effect_notheta_continuous.png"
PDF = RESULT / "figure3_kink_marginal_effect_notheta_continuous.pdf"

FONT_FAMILY = "DejaVu Sans"
MONO_FONT_FAMILY = "DejaVu Sans Mono"

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

BLUE = {
    "xlight": "#EAF1FE",
    "light": "#CEDFFE",
    "base": "#A3BEFA",
    "mid": "#5477C4",
    "dark": "#2E4780",
}

ORANGE = {
    "light": "#FFBDA1",
    "mid": "#CC6F47",
    "dark": "#804126",
}

def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    return rows


def col(rows, key):
    return np.array([float(r[key]) for r in rows], dtype=float)


def main():
    rows = sorted(read_rows(DATA), key=lambda r: int(r["grid_index"]))
    theta = col(rows, "theta")
    marginal_effect = col(rows, "marginal_effect")
    ci_low = col(rows, "ci_low")
    ci_high = col(rows, "ci_high")
    cutoff = float(rows[0]["cutoff"])
    ymin = min(ci_low.min(), marginal_effect.min(), 0)
    ymax = max(ci_high.max(), marginal_effect.max(), 0)
    pad = (ymax - ymin) * 0.16

    plt.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "figure.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "savefig.facecolor": TOKENS["surface"],
            "savefig.edgecolor": TOKENS["surface"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(8.9, 4.9))
    fig.patch.set_facecolor(TOKENS["surface"])
    ax.set_facecolor(TOKENS["panel"])

    ax.fill_between(
        theta,
        ci_low,
        ci_high,
        color=BLUE["light"],
        alpha=0.42,
        linewidth=0,
        label="95% confidence interval",
        zorder=1,
    )
    ax.plot(
        theta,
        marginal_effect,
        color=BLUE["dark"],
        linewidth=2.0,
        label="Marginal effect",
        zorder=3,
    )
    ax.axhline(0, color=TOKENS["ink"], linewidth=1.0, linestyle=(0, (4, 4)), alpha=0.75, zorder=2)
    ax.axvline(cutoff, color=ORANGE["mid"], linewidth=1.2, linestyle=(0, (4, 4)), zorder=2)

    ax.text(
        cutoff - (cutoff - theta.min()) * 0.55,
        ymax + pad * 0.28,
        "Debt-worsening region",
        color=ORANGE["dark"],
        fontsize=10.2,
        ha="center",
        va="top",
    )
    ax.text(
        cutoff + (theta.max() - cutoff) * 0.48,
        ymin - pad * 0.18,
        "Debt-improving region",
        color=BLUE["dark"],
        fontsize=10.2,
        ha="center",
        va="bottom",
    )
    ax.text(
        cutoff,
        ymin - pad * 0.64,
        f"c = {cutoff:.4f}",
        color=ORANGE["dark"],
        fontsize=9.2,
        ha="center",
        va="bottom",
        fontfamily=MONO_FONT_FAMILY,
    )

    ax.set_xlim(theta.min(), theta.max())
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xlabel("Readiness-based empirical theta", fontsize=10.5, color=TOKENS["ink"], labelpad=10)
    ax.set_ylabel("Marginal effect on next-period debt changes", fontsize=10.5, color=TOKENS["ink"], labelpad=10)
    ax.grid(axis="y", color=TOKENS["grid"], linewidth=0.8, linestyle=(0, (2, 3)))
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", colors=TOKENS["muted"], labelsize=9.5, length=0)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(MONO_FONT_FAMILY)

    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(TOKENS["axis"])
    ax.spines["bottom"].set_color(TOKENS["axis"])
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)

    fig.subplots_adjust(left=0.14, right=0.985, top=0.96, bottom=0.18)
    fig.savefig(PNG, dpi=300)
    fig.savefig(PDF)
    plt.close(fig)


if __name__ == "__main__":
    main()
