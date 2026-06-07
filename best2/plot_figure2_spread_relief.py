import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "result"
DATA = RESULT / "figure2_spread_relief_marginal_effects.csv"
PNG = RESULT / "figure2.png"
PDF = RESULT / "figure2.pdf"

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

def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    return rows


def as_float(row, key):
    return float(row[key])


def panel_rows(rows, panel):
    order = {"p10": 0, "p25": 1, "p50": 2, "p75": 3, "p90": 4}
    out = [r for r in rows if r["panel"] == panel]
    return sorted(out, key=lambda r: order[r["quantile"]])


def fmt_tick(panel, row):
    value = as_float(row, "grid_value")
    if panel == "A":
        return f"{row['quantile']}\n{100 * value:.1f}%"
    return f"{row['quantile']}\n{value:.3f}"


def apply_axis_style(ax):
    ax.set_facecolor(TOKENS["panel"])
    ax.grid(axis="y", color=TOKENS["grid"], linewidth=0.8, linestyle=(0, (2, 3)))
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", colors=TOKENS["muted"], labelsize=9, length=0)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(MONO_FONT_FAMILY)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(TOKENS["axis"])
    ax.spines["bottom"].set_color(TOKENS["axis"])
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)


def draw_panel(ax, rows, panel, title):
    x = np.arange(len(rows))
    relief = np.array([as_float(r, "relief") for r in rows])
    ci_low = np.array([as_float(r, "ci_low") for r in rows])
    ci_high = np.array([as_float(r, "ci_high") for r in rows])
    yerr = np.vstack([relief - ci_low, ci_high - relief])

    ax.errorbar(
        x,
        relief,
        yerr=yerr,
        fmt="o-",
        color=BLUE["dark"],
        ecolor=BLUE["mid"],
        markerfacecolor=TOKENS["panel"],
        markeredgecolor=BLUE["dark"],
        markeredgewidth=1.5,
        markersize=5.6,
        linewidth=1.6,
        elinewidth=1.2,
        capsize=4,
        capthick=1.2,
        zorder=3,
    )
    ax.axhline(0, color=TOKENS["ink"], linewidth=0.9, alpha=0.7, zorder=2)
    ax.set_title(title, loc="left", fontsize=12, color=TOKENS["ink"], fontweight="semibold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([fmt_tick(panel, r) for r in rows])
    ax.set_xlim(-0.35, len(rows) - 0.65)
    apply_axis_style(ax)


def main():
    rows = read_rows(DATA)
    rows_a = panel_rows(rows, "A")
    rows_b = panel_rows(rows, "B")
    if len(rows_a) != 5 or len(rows_b) != 5:
        raise RuntimeError("Expected five quantile rows for each panel.")

    all_lows = [as_float(r, "ci_low") for r in rows_a + rows_b]
    all_highs = [as_float(r, "ci_high") for r in rows_a + rows_b]
    ymin = min(min(all_lows), 0)
    ymax = max(max(all_highs), 0)
    pad = (ymax - ymin) * 0.12
    ylims = (ymin - pad, ymax + pad)

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

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.8), sharey=True)
    fig.patch.set_facecolor(TOKENS["surface"])

    draw_panel(axes[0], rows_a, "A", "Panel A. By Debt/GDP")
    draw_panel(axes[1], rows_b, "B", "Panel B. By GDP-adjusted\nVulnerability Performance")
    for ax in axes:
        ax.set_ylim(*ylims)

    axes[0].set_ylabel("Spread Relief = - dSpread / dReadinessGap", fontsize=10, color=TOKENS["ink"])
    axes[0].set_xlabel("Debt/GDP quantiles", fontsize=10, color=TOKENS["ink"], labelpad=10)
    axes[1].set_xlabel("vulnerability_delta quantiles", fontsize=10, color=TOKENS["ink"], labelpad=10)

    fig.subplots_adjust(left=0.08, right=0.985, top=0.86, bottom=0.19, wspace=0.12)
    fig.savefig(PNG, dpi=300)
    fig.savefig(PDF)
    plt.close(fig)


if __name__ == "__main__":
    main()
