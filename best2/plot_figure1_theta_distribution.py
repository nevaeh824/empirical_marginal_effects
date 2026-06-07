from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "result"

PANEL_PATH = RESULT / "theta_full_empirical_panel.csv"
CUTOFF_PATH = RESULT / "table7_deltaB_kink_selected_cutoff_notheta.csv"
RANKING_PATH = RESULT / "figure1_country_theta_ranking.csv"
PNG_PATH = RESULT / "figure1_theta_distribution_cutoff.png"
PDF_PATH = RESULT / "figure1_theta_distribution_cutoff.pdf"
SVG_PATH = RESULT / "figure1_theta_distribution_cutoff.svg"

FONT_FAMILY = ["DejaVu Sans", "Segoe UI", "Arial", "sans-serif"]
MONO_FONT_FAMILY = ["DejaVu Sans Mono", "Consolas", "monospace"]

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
    "neutral_light": "#E2E5EA",
    "neutral_mid": "#7A828F",
    "neutral_dark": "#464C55",
    "blue_xlight": "#EAF1FE",
    "blue_light": "#CEDFFE",
    "blue_base": "#A3BEFA",
    "blue_mid": "#5477C4",
    "blue_dark": "#2E4780",
}


def style_axis(ax):
    ax.set_facecolor(TOKENS["panel"])
    ax.grid(True, axis="y", color=TOKENS["grid"], linewidth=0.7)
    ax.grid(False, axis="x")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(TOKENS["axis"])
        ax.spines[spine].set_linewidth(0.8)
    ax.tick_params(axis="both", colors=TOKENS["muted"], labelsize=8.5, length=3)
    ax.xaxis.label.set_color(TOKENS["ink"])
    ax.yaxis.label.set_color(TOKENS["ink"])


def gaussian_kde(x, grid):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return np.zeros_like(grid)
    std = np.std(x, ddof=1)
    bandwidth = 1.06 * std * n ** (-1 / 5)
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        bandwidth = 0.01
    z = (grid[:, None] - x[None, :]) / bandwidth
    density = np.exp(-0.5 * z * z).sum(axis=1) / (n * bandwidth * np.sqrt(2 * np.pi))
    return density


def main():
    plt.rcParams.update(
        {
            "figure.facecolor": TOKENS["surface"],
            "savefig.facecolor": TOKENS["surface"],
            "axes.facecolor": TOKENS["panel"],
            "font.family": FONT_FAMILY,
            "axes.labelsize": 9.5,
            "axes.titlesize": 10.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    panel = pd.read_csv(PANEL_PATH)
    selected = pd.read_csv(CUTOFF_PATH)
    cutoff = float(
        selected.loc[selected["selection_rule"].eq("rss_min_cutoff"), "cutoff"].iloc[0]
    )

    theta = panel.loc[
        panel["theta_sample_full"].eq(1) & panel["theta_hat_full"].notna(),
        ["country_name", "iso3", "year", "theta_hat_full"],
    ].copy()
    theta["theta_hat_full"] = theta["theta_hat_full"].astype(float)

    country = (
        theta.groupby(["iso3", "country_name"], as_index=False)
        .agg(theta_mean=("theta_hat_full", "mean"), observations=("theta_hat_full", "size"))
        .sort_values("theta_mean", ascending=True)
        .reset_index(drop=True)
    )
    country["rank"] = np.arange(1, len(country) + 1)
    country["above_cutoff"] = country["theta_mean"] >= cutoff
    country.to_csv(RANKING_PATH, index=False)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(11.2, 4.9),
        gridspec_kw={"width_ratios": [1.05, 1.25], "wspace": 0.30},
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.89, bottom=0.16)

    ax = axes[0]
    style_axis(ax)
    bins = np.linspace(theta["theta_hat_full"].min(), theta["theta_hat_full"].max(), 42)
    hist, edges = np.histogram(theta["theta_hat_full"], bins=bins, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    ax.bar(
        centers,
        hist,
        width=widths,
        align="center",
        color=TOKENS["blue_base"],
        edgecolor=TOKENS["blue_dark"],
        linewidth=0.35,
        alpha=0.72,
    )
    kde_grid = np.linspace(theta["theta_hat_full"].min(), theta["theta_hat_full"].max(), 400)
    kde_values = gaussian_kde(theta["theta_hat_full"], kde_grid)
    ax.plot(kde_grid, kde_values, color=TOKENS["blue_dark"], linewidth=1.4)
    ax.axvline(cutoff, color=TOKENS["neutral_dark"], linestyle=(0, (4, 3)), linewidth=1.1)
    ax.annotate(
        "Preferred cutoff",
        xy=(cutoff, ax.get_ylim()[1] * 0.70),
        xytext=(0.145, ax.get_ylim()[1] * 0.82),
        arrowprops={
            "arrowstyle": "-",
            "color": TOKENS["neutral_dark"],
            "linewidth": 0.8,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        ha="left",
        va="center",
        fontsize=8.5,
        color=TOKENS["neutral_dark"],
    )
    ax.set_title("A. Country-year distribution", loc="left", pad=9, color=TOKENS["ink"])
    ax.set_xlabel(r"$\widehat{\theta}^{F}_{it}$")
    ax.set_ylabel("Density")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(6))

    ax = axes[1]
    style_axis(ax)
    colors = np.where(country["above_cutoff"], TOKENS["blue_mid"], TOKENS["neutral_light"])
    edgecolors = np.where(country["above_cutoff"], TOKENS["blue_dark"], TOKENS["neutral_mid"])
    ax.scatter(
        country["theta_mean"],
        country["rank"],
        s=26,
        c=colors,
        edgecolors=edgecolors,
        linewidths=0.45,
        zorder=3,
    )
    ax.axvline(cutoff, color=TOKENS["neutral_dark"], linestyle=(0, (4, 3)), linewidth=1.1)
    ax.set_title(
        r"B. Countries ranked by sample-average $\widehat{\theta}^{F}_{it}$",
        loc="left",
        pad=9,
        color=TOKENS["ink"],
    )
    ax.set_xlabel(r"Country mean of $\widehat{\theta}^{F}_{it}$")
    ax.set_ylabel("Country rank")
    ax.set_ylim(0, len(country) + 2)
    ax.yaxis.set_major_locator(mticker.FixedLocator([1, 15, 30, 45, 60]))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(6))
    label_rows = pd.concat(
        [
            country.head(1),
            country.tail(4),
        ]
    ).drop_duplicates("iso3")
    for _, row in label_rows.iterrows():
        x = row["theta_mean"]
        y = row["rank"]
        ha = "left"
        dx = 0.012
        if x > country["theta_mean"].quantile(0.92):
            ha = "right"
            dx = -0.018
        ax.text(
            x + dx,
            y,
            row["iso3"],
            ha=ha,
            va="center",
            fontsize=7.4,
            color=TOKENS["neutral_dark"],
            family=MONO_FONT_FAMILY,
        )

    ax.text(
        cutoff + 0.012,
        7.2,
        f"cutoff = {cutoff:.3f}",
        ha="left",
        va="center",
        fontsize=8.3,
        color=TOKENS["neutral_dark"],
    )

    fig.text(
        0.075,
        0.035,
        (
            "Notes: The cutoff is the RSS-minimizing cutoff from the kinked marginal-effect model "
            "without direct theta controls. Country means use the full-interaction theta estimation sample."
        ),
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=TOKENS["muted"],
    )

    for path in [PNG_PATH, PDF_PATH, SVG_PATH]:
        fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {PNG_PATH}")
    print(f"Saved {PDF_PATH}")
    print(f"Saved {SVG_PATH}")
    print(f"Saved {RANKING_PATH}")


if __name__ == "__main__":
    main()
