import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "result"
REPORT = ROOT / "best2_readiness_delta_vulnerability_delta_report.md"
COMBO = "readiness_delta100__vulnerability_delta100"


def read_csv_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def read_csv_dicts(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def tex_cells(line):
    line = line.strip()
    if line.endswith(r"\\"):
        line = line[:-2].strip()
    return [cell.strip() for cell in line.split("&")]


def parse_estimate_tex(path, labels):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    out = {}
    stats = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        for key, label in labels.items():
            if stripped.startswith(label):
                coef_cells = tex_cells(stripped)[1:]
                t_cells = []
                if i + 1 < len(lines):
                    next_cells = tex_cells(lines[i + 1].strip())
                    if next_cells and next_cells[0] == "":
                        t_cells = next_cells[1:]
                out[key] = {"coef": coef_cells, "t": t_cells}
        if stripped.startswith("Countries"):
            stats["Countries"] = tex_cells(stripped)[1:]
        elif stripped.startswith("Observations"):
            stats["Observations"] = tex_cells(stripped)[1:]
        elif stripped.startswith("Adjusted"):
            stats["Adjusted R2"] = tex_cells(stripped)[1:]
    return out, stats


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(headers) - 1)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def csv_to_md(path):
    rows = read_csv_rows(path)
    if not rows:
        return ""
    return md_table(rows[0], rows[1:])


def csv_to_md_if_exists(path):
    if not path.exists():
        return "_Not generated._"
    return csv_to_md(path)


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except ValueError:
        return None


def stars(p):
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt_float(value, digits=3):
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):,.{digits}f}"
    except ValueError:
        return str(value)


def fmt_pct(value, digits=2):
    if value is None or value == "":
        return ""
    try:
        return f"{100 * float(value):,.{digits}f}%"
    except ValueError:
        return str(value)


def percentile(values, p):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    weight = pos - lo
    return vals[lo] * (1 - weight) + vals[hi] * weight


def kink_selected_row(path, rule="rss_min_cutoff"):
    if not path.exists():
        return None
    for row in read_csv_dicts(path):
        if row.get("selection_rule") == rule:
            return row
    return None


def kink_interpretation(path, version_label):
    row = kink_selected_row(path)
    if not row:
        return f"{version_label}: kink results were not generated."

    b_low = safe_float(row.get("b_low"))
    b_high = safe_float(row.get("b_high"))
    p_low_pos = safe_float(row.get("p_low_positive"))
    p_high_neg = safe_float(row.get("p_high_negative"))
    low_sign = b_low is not None and b_low > 0
    high_sign = b_high is not None and b_high < 0
    low_meaningful = low_sign and p_low_pos is not None and p_low_pos < 0.10
    high_meaningful = high_sign and p_high_neg is not None and p_high_neg < 0.10

    prefix = f"{version_label}: "
    if low_meaningful and high_meaningful:
        return (
            prefix
            + "the segmented marginal-effect model identifies an empirical zero-crossing pattern. "
            + "Below the cutoff, adaptation investment raises next-period debt; above the cutoff, adaptation investment reduces next-period debt. "
            + "This supports the interpretation of $$\\widehat{\\theta}^{F}_{it}$$ as a debt-improving capacity index."
        )
    if low_meaningful and high_sign:
        return (
            prefix
            + "the evidence supports a debt-worsening effect of adaptation in the low-theta region, "
            + "but the debt-improving effect in the high-theta region is weaker."
        )
    if high_meaningful and low_sign:
        return (
            prefix
            + "the evidence supports a debt-improving effect of adaptation in the high-theta region, "
            + "but the debt-worsening effect in the low-theta region is weaker."
        )
    return prefix + "the current data do not support the single-crossing segmented marginal-effect specification."


def kink_robustness_table(items):
    rows = []
    for label, suffix in items:
        path = RESULT / f"table7_deltaB_kink_selected_cutoff{suffix}.csv"
        row = kink_selected_row(path)
        if not row:
            rows.append([label, "", "", "", "", "", "", "", ""])
            continue
        rows.append(
            [
                label,
                fmt_float(row.get("cutoff")),
                row.get("sign_ok", ""),
                f"{fmt_float(row.get('b_low'))}{stars(row.get('p_low'))}",
                fmt_float(row.get("p_low_positive")),
                f"{fmt_float(row.get('b_high'))}{stars(row.get('p_high'))}",
                fmt_float(row.get("p_high_negative")),
                row.get("N_model", ""),
                fmt_float(row.get("r2")),
            ]
        )
    return md_table(
        [
            "Version",
            "RSS cutoff",
            "Sign OK",
            "$$a$$",
            "$$p(a>0)$$",
            "$$b$$",
            "$$p(b<0)$$",
            "N",
            "Adj. $$R^2$$",
        ],
        rows,
    )


def compact_group_table(path):
    rows = []
    for row in read_csv_dicts(path):
        coef = f"{fmt_float(row['b_G'])}{stars(row['p_G'])}"
        rows.append(
            [
                row["group"],
                row["split"],
                fmt_float(row["cutoff_low"]),
                fmt_float(row["cutoff_high"]),
                coef,
                fmt_float(row["t_G"]),
                fmt_float(row["p_G"]),
                row["N_model"],
                row["N_countries"],
                fmt_float(row["r2"]),
            ]
        )
    return md_table(
        [
            "Group",
            "Split",
            "Cutoff low",
            "Cutoff high",
            "$$G_{it}$$",
            "t-stat.",
            "p-value",
            "N",
            "Countries",
            "Adj. $$R^2$$",
        ],
        rows,
    )


def country_theta_screen_tables():
    cutoff_row = kink_selected_row(RESULT / "table7_deltaB_kink_selected_cutoff_notheta.csv")
    if not cutoff_row:
        return "_Preferred no-theta cutoff was not generated._"
    cutoff = safe_float(cutoff_row.get("cutoff"))
    if cutoff is None:
        return "_Preferred no-theta cutoff is missing._"

    country_years = {}
    for row in read_csv_dicts(RESULT / "theta_full_empirical_panel.csv"):
        if row.get("theta_sample_full") not in {"1", "1.0"}:
            continue
        theta = safe_float(row.get("theta_hat_full"))
        mg = safe_float(row.get("mG_hat_full"))
        debt = safe_float(row.get("debt_ratio"))
        year = safe_float(row.get("year"))
        if theta is None or mg is None or debt is None or year is None:
            continue
        key = (row.get("iso3", ""), row.get("country_name", ""))
        country_years.setdefault(key, []).append(
            {
                "year": int(year),
                "theta": theta,
                "mg": mg,
                "debt": debt,
            }
        )

    countries = []
    for (iso3, country_name), values in country_years.items():
        if not values:
            continue
        countries.append(
            {
                "iso3": iso3,
                "country_name": country_name,
                "years": len(values),
                "first_year": min(v["year"] for v in values),
                "last_year": max(v["year"] for v in values),
                "theta_mean": sum(v["theta"] for v in values) / len(values),
                "theta_min": min(v["theta"] for v in values),
                "theta_max": max(v["theta"] for v in values),
                "mg_mean": sum(v["mg"] for v in values) / len(values),
                "debt_mean": sum(v["debt"] for v in values) / len(values),
            }
        )

    debt_median = percentile([c["debt_mean"] for c in countries], 0.50)
    mg_q25 = percentile([c["mg_mean"] for c in countries], 0.25)
    mg_q75 = percentile([c["mg_mean"] for c in countries], 0.75)
    high = sorted(
        [
            c
            for c in countries
            if c["debt_mean"] < debt_median
            and c["theta_min"] > cutoff
            and c["mg_mean"] >= mg_q75
        ],
        key=lambda c: (-c["mg_mean"], -c["theta_mean"]),
    )
    low = sorted(
        [
            c
            for c in countries
            if c["debt_mean"] > debt_median
            and c["theta_max"] < cutoff
            and c["mg_mean"] <= mg_q25
        ],
        key=lambda c: (c["mg_mean"], c["theta_mean"]),
    )

    high_rows = [
        [
            c["country_name"],
            c["iso3"],
            f"{c['first_year']}--{c['last_year']}",
            c["years"],
            fmt_pct(c["debt_mean"]),
            fmt_float(c["theta_mean"], 6),
            fmt_float(c["theta_min"], 6),
            fmt_float(c["mg_mean"], 6),
        ]
        for c in high
    ]
    low_rows = [
        [
            c["country_name"],
            c["iso3"],
            f"{c['first_year']}--{c['last_year']}",
            c["years"],
            fmt_pct(c["debt_mean"]),
            fmt_float(c["theta_mean"], 6),
            fmt_float(c["theta_max"], 6),
            fmt_float(c["mg_mean"], 6),
        ]
        for c in low
    ]

    return "\n\n".join(
        [
            (
                "Screening thresholds use country-level means: preferred no-theta cutoff "
                f"$$c={fmt_float(cutoff, 6)}$$, mean debt/GDP median "
                f"{fmt_pct(debt_median)}, bottom-quartile $$\\widehat{{m}}^{{G,F}}_{{it}}$$ "
                f"{fmt_float(mg_q25, 6)}, and top-quartile $$\\widehat{{m}}^{{G,F}}_{{it}}$$ "
                f"{fmt_float(mg_q75, 6)}. The always-above and always-below conditions are evaluated year by year."
            ),
            "Low-debt countries with $$\\widehat{\\theta}^{F}_{it}$$ always above the cutoff and top-quartile marginal spread relief:",
            md_table(
                [
                    "Country",
                    "ISO3",
                    "Sample period",
                    "Years",
                    "Mean debt/GDP",
                    "Mean theta",
                    "Min theta",
                    "Mean $$\\widehat{m}^{G,F}_{it}$$",
                ],
                high_rows,
            ),
            "High-debt countries with $$\\widehat{\\theta}^{F}_{it}$$ always below the cutoff and bottom-quartile marginal spread relief:",
            md_table(
                [
                    "Country",
                    "ISO3",
                    "Sample period",
                    "Years",
                    "Mean debt/GDP",
                    "Mean theta",
                    "Max theta",
                    "Mean $$\\widehat{m}^{G,F}_{it}$$",
                ],
                low_rows,
            ),
        ]
    )


def file_rows(path):
    if path.suffix.lower() != ".csv":
        return ""
    return str(max(0, len(read_csv_rows(path)) - 1))


def build_report():
    labels = {
        "G": r"$$G_{it}$$",
        "B": r"$$B_{it}$$",
        "X": r"$$X_{it}$$",
        "E": r"$$E_{it}$$",
        "GxB": r"$$G_{it}\times B_{it}$$",
        "GxX": r"$$G_{it}\times X_{it}$$",
        "GxE": r"$$G_{it}\times E_{it}$$",
    }

    table2, table2_stats = parse_estimate_tex(RESULT / "table2_baseline_fe_periods.tex", labels)
    table3, table3_stats = parse_estimate_tex(RESULT / "table3_heterogeneity_theta.tex", labels)
    table6_full, table6_full_stats = parse_estimate_tex(
        RESULT / "table6_fullinteraction_theta_regression.tex", labels
    )
    table2_rows = []
    for key, label in [("G", "$$G_{it}$$"), ("B", "$$B_{it}$$"), ("X", "$$X_{it}$$")]:
        rec = table2.get(key, {"coef": [""], "t": [""]})
        table2_rows.append([label, rec["coef"][0] if rec["coef"] else "", rec["t"][0] if rec["t"] else ""])
    table2_rows.extend(
        [
            ["Controls", "Yes", ""],
            ["Country FE", "Yes", ""],
            ["Year FE", "Yes", ""],
            ["Sample period", "1995--2023", ""],
            ["Countries", table2_stats.get("Countries", [""])[0], ""],
            ["Observations", table2_stats.get("Observations", [""])[0], ""],
            ["Adjusted $$R^2$$", table2_stats.get("Adjusted R2", [""])[0], ""],
        ]
    )

    table3_rows = []
    for key, label in [
        ("G", "$$G_{it}$$"),
        ("B", "$$B_{it}$$"),
        ("X", "$$X_{it}$$"),
        ("GxB", "$$G_{it} \\times B_{it}$$"),
        ("GxX", "$$G_{it} \\times X_{it}$$"),
    ]:
        rec = table3.get(key, {"coef": ["", "", ""], "t": ["", "", ""]})
        rec_full = table6_full.get(key, {"coef": [""], "t": [""]})
        table3_rows.append([label] + rec["coef"] + [rec_full["coef"][0] if rec_full["coef"] else ""])
        table3_rows.append(["t-stat."] + rec["t"] + [rec_full["t"][0] if rec_full["t"] else ""])
    table3_rows.extend(
        [
            ["Controls"] + ["Yes", "Yes", "Yes", "Yes"],
            ["$$G_{it} \\times \\mathbf{Z}_{it}$$ controls"] + ["No", "No", "No", "Yes"],
            ["Country FE"] + ["Yes", "Yes", "Yes", "Yes"],
            ["Year FE"] + ["Yes", "Yes", "Yes", "Yes"],
            ["Countries"]
            + table3_stats.get("Countries", ["", "", ""])
            + table6_full_stats.get("Countries", [""]),
            ["Observations"]
            + table3_stats.get("Observations", ["", "", ""])
            + table6_full_stats.get("Observations", [""]),
            ["Adjusted $$R^2$$"]
            + table3_stats.get("Adjusted R2", ["", "", ""])
            + table6_full_stats.get("Adjusted R2", [""]),
        ]
    )

    inventory = []
    for path in sorted(RESULT.iterdir()):
        inventory.append(
            [
                path.name,
                f"{path.stat().st_size:,}",
                file_rows(path),
            ]
        )

    log_path = RESULT / "paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.log"
    log_text = log_path.read_text(encoding="utf-8-sig", errors="ignore")
    stata_errors = len(re.findall(r"(?m)^r\([0-9]+\);", log_text))
    done = "Done. Retained Paper B outputs" in log_text

    kink_with_theta = RESULT / "table7_deltaB_kink_selected_cutoff.csv"
    kink_without_theta = RESULT / "table7_deltaB_kink_selected_cutoff_notheta.csv"
    kink_with_theta_interpretation = kink_interpretation(kink_with_theta, "With theta controls")
    kink_without_theta_interpretation = kink_interpretation(kink_without_theta, "Without theta controls")
    kink_with_theta_robustness = kink_robustness_table(
        [
            ("Main 10-90", ""),
            ("Trim 15-85", "_trim15"),
            ("Trim 20-80", "_trim20"),
            ("Country cluster", "_cluster"),
            ("Lagged theta", "_lagtheta"),
            ("Horizon t+2", "_h2"),
            ("Horizon t+3", "_h3"),
        ]
    )
    kink_without_theta_robustness = kink_robustness_table(
        [
            ("Main 10-90", "_notheta"),
            ("Trim 15-85", "_notheta_trim15"),
            ("Trim 20-80", "_notheta_trim20"),
            ("Country cluster", "_notheta_cluster"),
            ("Lagged theta", "_notheta_lagtheta"),
            ("Horizon t+2", "_notheta_h2"),
            ("Horizon t+3", "_notheta_h3"),
        ]
    )

    lines = [
        f"# Best2 Standalone Report: `{COMBO}`",
        "",
        "## 1. Reproduction Files",
        "",
        "- Stata code: `best2/paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do`.",
        "- Result directory: `best2/result`.",
        "- Report generator: `best2/generate_best2_report.py`.",
        "- Figure 1 generator: `best2/plot_figure1_theta_distribution.py`.",
        "- This report: `best2/best2_readiness_delta_vulnerability_delta_report.md`.",
        "",
        "Run from the project root:",
        "",
        "```powershell",
        "& 'C:\\Environment_tools\\Stata18\\StataMP-64.exe' /e do 'best2\\paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do' 'C:\\Users\\chenyu\\Desktop\\emoirical0530'",
        "python best2\\plot_figure1_theta_distribution.py",
        "python best2\\generate_best2_report.py",
        "```",
        "",
        "## 2. Data Preprocessing",
        "",
        "Source panel: `cleaned_imf_like_panel_1995_2023.csv`.",
        "",
        "The standalone script fixes the empirical proxy pair as:",
        "",
        "$$G_{it}=0.01\\times readiness\\_delta100_{it},\\qquad X_{it}=0.01\\times vulnerability\\_delta100_{it}.$$",
        "",
        "Other transformed variables are:",
        "",
        "$$s_{it}=0.01\\times bond\\_spreads_{it},\\quad B_{it}=0.01\\times debt\\_gdp_{it}.$$",
        "",
        "The control vector is",
        "",
        "$$\\mathbf{Z}_{it}=\\{lnrgdp, growth, inflation\\_cpi, OB\\_gdp, reserves, gee, rqe, tt\\},$$",
        "",
        "and every control in `Z` is also multiplied by 0.01 before estimation. The script builds",
        "",
        "$$G_{it} \\times B_{it},\\quad G_{it} \\times X_{it},\\quad G_{it} \\times \\mathbf{Z}_{it}.$$",
        "",
        "All regressions exclude the United States, use the 1995--2023 panel, include country and year fixed effects unless stated otherwise, and report robust t-statistics.",
        "",
        "## 3. Regression Formulas",
        "",
        "### Table 2 Baseline Spread Model",
        "",
        "$$s_{it}=\\alpha_i+\\tau_t+\\beta_GG_{it}+\\beta_BB_{it}+\\beta_XX_{it}+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+u_{it}.$$",
        "",
        "### Table 3 Heterogeneity and Full-Interaction Spread Models",
        "",
        "Debt heterogeneity:",
        "",
        "$$s_{it}=\\alpha_i+\\tau_t+\\beta_GG_{it}+\\beta_BB_{it}+\\beta_XX_{it}+\\beta_{GB}(G_{it} \\times B_{it})+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+u_{it}.$$",
        "",
        "Climate-risk heterogeneity:",
        "",
        "$$s_{it}=\\alpha_i+\\tau_t+\\beta_GG_{it}+\\beta_BB_{it}+\\beta_XX_{it}+\\beta_{GX}(G_{it} \\times X_{it})+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+u_{it}.$$",
        "",
        "Full Table 3 interaction:",
        "",
        "$$s_{it}=\\alpha_i+\\tau_t+\\beta_GG_{it}+\\beta_BB_{it}+\\beta_XX_{it}+\\beta_{GB}(G_{it} \\times B_{it})+\\beta_{GX}(G_{it} \\times X_{it})+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+u_{it}.$$",
        "",
        "### Full-Interaction Empirical Theta",
        "",
        "$$s_{it}=\\alpha_i+\\tau_t+\\beta_GG_{it}+\\beta_BB_{it}+\\beta_{GB}(G_{it} \\times B_{it})+\\beta_{GX}(G_{it} \\times X_{it})+\\beta_XX_{it}+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\boldsymbol{\\Gamma}_{GZ}'(G_{it} \\times \\mathbf{Z}_{it})+u_{it}.$$",
        "",
        "$$\\frac{\\partial s_{it}}{\\partial G_{it}}=\\beta_G+\\beta_{GB}B_{it}+\\beta_{GX}X_{it}+\\boldsymbol{\\Gamma}_{GZ}'\\mathbf{Z}_{it}.$$",
        "",
        "$$\\widehat{m}^{G,F}_{it}=-\\frac{\\partial \\widehat{s}_{it}}{\\partial G_{it}},\\qquad \\widehat{\\theta}^{F}_{it}=B_{it}\\widehat{m}^{G,F}_{it}.$$",
        "",
        "### Debt-Change Models",
        "",
        "Define next-period debt change as",
        "",
        "$$\\Delta B_{i,t+1}=B_{i,t+1}-B_{it}.$$",
        "",
        "Baseline:",
        "",
        "$$\\Delta B_{i,t+1}=\\alpha_i+\\tau_t+\\lambda_0G_{it}+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\varepsilon_{it}.$$",
        "",
        "Continuous Full-theta:",
        "",
        "$$\\Delta B_{i,t+1}=\\alpha_i+\\tau_t+\\lambda_0G_{it}+\\lambda_1(G_{it} \\times \\widehat{\\theta}^{F}_{it})+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\varepsilon_{it}.$$",
        "",
        "Full-theta dynamics:",
        "",
        "$$\\Delta B_{i,t+1}=\\alpha_i+\\tau_t+\\lambda_0G_{it}+\\lambda_1(G_{it} \\times \\widehat{\\theta}^{F}_{it})+\\lambda_2\\widehat{\\theta}^{F}_{it}+\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\varepsilon_{it}.$$",
        "",
        "Grouped heterogeneity estimates the baseline debt-change equation within theta, debt-ratio, or marginal-relief quantile groups.",
        "",
        "## 4. Main Tables",
        "",
        "### Table 2. Baseline Fixed-Effects Estimates",
        "",
        md_table(["Variable", "Coefficient", "t-stat."], table2_rows),
        "",
        "### Table 3. Heterogeneity and Full-Interaction Spread Models",
        "",
        md_table(
            [
                "Variable",
                "Debt heterogeneity",
                "Climate-risk heterogeneity",
                "Full interaction",
                "Full interaction + $$G_{it} \\times \\mathbf{Z}_{it}$$",
            ],
            table3_rows,
        ),
        "",
        "### Table 6. Theta Descriptive Statistics",
        "",
        csv_to_md(RESULT / "table6_theta_descriptive_stats.csv"),
        "",
        "### Figure 1. Distribution of `theta_hat_full`",
        "",
        "![Figure 1. Distribution of theta_hat_full and country-average ranking](result/figure1_theta_distribution_cutoff.png)",
        "",
        "Notes: The left panel plots the country-year distribution of $$\\widehat{\\theta}^{F}_{it}$$; the right panel ranks countries by sample-average $$\\widehat{\\theta}^{F}_{it}$$. The dashed vertical line marks the preferred cutoff from the kinked marginal-effect model without direct theta controls.",
        "",
        "### Table 6.1. Country Screens Around the Preferred Cutoff",
        "",
        country_theta_screen_tables(),
        "",
        "### Table 6.2. Full-Theta Debt-Level Dynamics Regression",
        "",
        csv_to_md(RESULT / "table6_2_debt_level_dynamics_regression.csv"),
        "",
        "### Table 7.0. Baseline Debt-Change Regression",
        "",
        csv_to_md(RESULT / "table7_0_baseline_debt_change_regression.csv"),
        "",
        "### Table 7. Continuous Full-Theta Debt Regression",
        "",
        csv_to_md(RESULT / "table7_continuous_theta_debt_regression.csv"),
        "",
        "### Combined Table 6.2/6.3/7 Debt-Change Regressions",
        "",
        csv_to_md(RESULT / "table6_2_6_3_7_debt_change_regressions.csv"),
        "",
        "### Theta-Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_theta_group_heterogeneity.csv"),
        "",
        "### Debt-Ratio Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_B_group_heterogeneity.csv"),
        "",
        "### Marginal-Relief Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_mG_group_heterogeneity.csv"),
        "",
        "### Single-Crossing Kink Marginal-Effect Model",
        "",
        "This is not a standard panel threshold model. The kink model directly estimates whether the marginal debt effect of readiness crosses zero at an empirical cutoff.",
        "",
        "$$\\Delta B_{i,t+1}=\\alpha_i+\\tau_t+aG_{it}(c-\\widehat{\\theta}^{F}_{it})_++bG_{it}(\\widehat{\\theta}^{F}_{it}-c)_++\\rho_1\\widehat{\\theta}^{F}_{it}+\\rho_2(\\widehat{\\theta}^{F}_{it}-c)_++\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\varepsilon_{it}.$$",
        "",
        "$$m(\\theta;c)=a(c-\\theta)_+ + b(\\theta-c)_+.$$",
        "",
        "The theory-implied sign pattern is $$a>0$$ and $$b<0$$: adaptation raises next-period debt below the cutoff but reduces next-period debt above the cutoff.",
        "",
        "#### With Theta Controls",
        "",
        "This version includes $$\\widehat{\\theta}^{F}_{it}$$ and $$(\\widehat{\\theta}^{F}_{it}-c)_+$$ as direct controls.",
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_selected_cutoff.csv"),
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_marginal_effects.csv"),
        "",
        kink_with_theta_interpretation,
        "",
        "Robustness checks for the with-theta-controls version:",
        "",
        kink_with_theta_robustness,
        "",
        "#### Without Theta Controls",
        "",
        "This version keeps the two kinked readiness terms but omits $$\\widehat{\\theta}^{F}_{it}$$ and $$(\\widehat{\\theta}^{F}_{it}-c)_+$$ as direct controls.",
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_selected_cutoff_notheta.csv"),
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_marginal_effects_notheta.csv"),
        "",
        kink_without_theta_interpretation,
        "",
        "Robustness checks for the without-theta-controls version:",
        "",
        kink_without_theta_robustness,
        "",
        "Full cutoff grids are exported as machine-readable CSV files and are not expanded inline: `table7_deltaB_kink_cutoff_grid*.csv`.",
        "",
        "## 5. Result File Inventory",
        "",
        "Large machine-readable support files are saved in `best2/result` and are not expanded inline: `theta_full_empirical_panel.csv` and `table7_deltaB_kink_cutoff_grid*.csv`.",
        "",
        md_table(["File", "Bytes", "CSV rows"], inventory),
        "",
        "## 6. Verification",
        "",
        f"- Stata runtime error count from `r(...)`: `{stata_errors}`.",
        f"- Stata completion marker found: `{done}`.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build_report()
