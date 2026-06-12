import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "result"
REPORT = ROOT / "appendixC_readiness_vulnerability_report.md"
COMBO = "readiness100__vulnerability100"


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


def table1_descriptive_stats(path):
    if not path.exists():
        return "_Table 1 descriptive statistics were not generated._"
    rows = []
    symbols = {
        "s_it": "$$s_{it}$$",
        "G_it": "$$G_{it}$$",
        "B_it": "$$B_{it}$$",
        "X_it": "$$X_{it}$$",
    }
    for row in read_csv_dicts(path):
        symbol = row.get("symbol", "")
        rows.append(
            [
                row.get("block", ""),
                row.get("variable", ""),
                symbols.get(symbol, f"`{symbol}`" if symbol else ""),
                f"`{row.get('source', '')}`",
                row.get("N", ""),
                fmt_float(row.get("mean")),
                fmt_float(row.get("sd")),
                fmt_float(row.get("median")),
                fmt_float(row.get("min")),
                fmt_float(row.get("max")),
            ]
        )
    return md_table(
        [
            "Block",
            "Variable",
            "Symbol",
            "Source",
            "N",
            "Mean",
            "SD",
            "Median",
            "Min",
            "Max",
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


def coef_t_cell(row, b_key, t_key, p_key):
    b = safe_float(row.get(b_key))
    if b is None:
        return ""
    t = safe_float(row.get(t_key))
    t_part = "" if t is None else f" ({fmt_float(t)})"
    return f"{fmt_float(b)}{stars(row.get(p_key))}{t_part}"


def appendix_debt_control_variants_table(path):
    if not path.exists():
        return "_Appendix debt-change control variants were not generated._"
    rows = []
    for row in read_csv_dicts(path):
        rows.append(
            [
                row.get("model", ""),
                row.get("control_set", ""),
                coef_t_cell(row, "b_G", "t_G", "p_G"),
                coef_t_cell(row, "b_Gtheta", "t_Gtheta", "p_Gtheta"),
                coef_t_cell(row, "b_theta", "t_theta", "p_theta"),
                coef_t_cell(row, "b_B", "t_B", "p_B"),
                coef_t_cell(row, "b_X", "t_X", "p_X"),
                "Yes" if row.get("z_controls") in {"1", "1.0"} else "No",
                row.get("N_model", ""),
                fmt_float(row.get("r2")),
            ]
        )
    return md_table(
        [
            "Model",
            "Control set",
            "$$G_{it}$$",
            "$$G_{it}\\times\\widehat{\\theta}^{F}_{it}$$",
            "$$\\widehat{\\theta}^{F}_{it}$$",
            "$$B_{it}$$",
            "$$X_{it}$$",
            "$$\\mathbf{Z}_{it}$$",
            "N",
            "Adj. $$R^2$$",
        ],
        rows,
    )


def kink_control_variant_table(items):
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
            "Control set",
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

    log_path = RESULT / "paperC_appendixC_readiness_vulnerability_1995_2023_tables.log"
    log_text = log_path.read_text(encoding="utf-8-sig", errors="ignore")
    stata_errors = len(re.findall(r"(?m)^r\([0-9]+\);", log_text))
    done = "Done. Retained Appendix C outputs" in log_text

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
    kink_without_theta_control_variants = kink_control_variant_table(
        [
            ("Z+B+X", "_notheta_zbx"),
            ("B+X", "_notheta_bx"),
            ("None", "_notheta_none"),
        ]
    )
    kink_with_theta_control_variants = kink_control_variant_table(
        [
            ("Z+B+X", "_withtheta_zbx"),
            ("B+X", "_withtheta_bx"),
            ("None", "_withtheta_none"),
        ]
    )

    lines = [
        f"# Appendix C Standalone Report: `{COMBO}`",
        "",
        "## 1. Reproduction Files",
        "",
        "- Stata code: `appendixC/paperC_appendixC_readiness_vulnerability_1995_2023_tables.do`.",
        "- Result directory: `appendixC/result`.",
        "- Report generator: `appendixC/generate_appendixC_report.py`.",
        "- Figure 1 generator: `appendixC/plot_figure1_theta_distribution.py`.",
        "- Figure 2 generator: `appendixC/plot_figure2_spread_relief.py`.",
        "- Figure 3 generator: `appendixC/plot_figure3_kink_curve.py`.",
        "- This report: `appendixC/appendixC_readiness_vulnerability_report.md`.",
        "",
        "Run from the project root:",
        "",
        "```powershell",
        "& 'C:\\Environment_tools\\Stata18\\StataMP-64.exe' /e do 'appendixC\\paperC_appendixC_readiness_vulnerability_1995_2023_tables.do' 'C:\\Users\\chenyu\\Desktop\\0606'",
        "python appendixC\\plot_figure1_theta_distribution.py",
        "python appendixC\\plot_figure2_spread_relief.py",
        "python appendixC\\plot_figure3_kink_curve.py",
        "python appendixC\\generate_appendixC_report.py",
        "```",
        "",
        "## 2. Data Preprocessing",
        "",
        "Source panel: `cleaned_imf_like_panel_1995_2023.csv`.",
        "",
        "The standalone script fixes the empirical proxy pair as:",
        "",
        "$$G_{it}=0.01\\times readiness100_{it},\\qquad X_{it}=0.01\\times vulnerability100_{it}.$$",
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
        "### Table 1. Post-Preprocessing Descriptive Statistics",
        "",
        "Statistics use the post-preprocessing non-U.S. 1995--2023 panel. Each row is computed on nonmissing observations for that variable after the 0.01 scaling described in Section 2.",
        "",
        table1_descriptive_stats(RESULT / "table1_preprocessed_descriptive_stats.csv"),
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
        "### Table 4. Theta Descriptive Statistics",
        "",
        csv_to_md(RESULT / "table6_theta_descriptive_stats.csv"),
        "",
        "### Figure 1. Distribution of `theta_hat_full`",
        "",
        "![Figure 1. Distribution of theta_hat_full and country-average ranking](result/figure1_theta_distribution_cutoff.png)",
        "",
        "Notes: The left panel plots the country-year distribution of $$\\widehat{\\theta}^{F}_{it}$$; the right panel ranks countries by sample-average $$\\widehat{\\theta}^{F}_{it}$$. The dashed vertical line marks the preferred cutoff from the kinked marginal-effect model without direct theta controls.",
        "",
        "Construction details: Figure 1 is generated by `appendixC/plot_figure1_theta_distribution.py` from `theta_full_empirical_panel.csv`. The script keeps observations with `theta_sample_full == 1` and nonmissing `theta_hat_full`, which is the empirical theta implied by the full-interaction spread model. The left panel uses the retained country-year observations to draw a histogram and a kernel-density overlay for $$\\widehat{\\theta}^{F}_{it}$$. The right panel collapses the same sample to country-level averages, orders countries from lowest to highest average theta, and plots the resulting ranking. The vertical dashed cutoff is read from `table7_deltaB_kink_selected_cutoff_notheta.csv`, so the figure uses the preferred cutoff from the main without-theta-controls kink specification rather than a visually chosen threshold.",
        "",
        "### Figure 2. Marginal Spread Relief from Table 3 Full Interaction",
        "",
        "![Figure 2. Marginal spread relief from readiness performance](result/figure2.png)",
        "",
        "Notes: The figure plots the negative marginal effect of GDP-adjusted readiness performance on sovereign spreads, based on the Table 3 full-interaction specification. In Panel A, vulnerability_delta is fixed at its median. In Panel B, Debt/GDP is fixed at its median. Higher vulnerability_delta indicates lower vulnerability relative to GDP-predicted vulnerability; hence a downward slope in Panel B means stronger spread relief among more vulnerable countries.",
        "",
        "Construction details: Figure 2 is generated in two steps. First, the Stata script re-estimates the Table 3 full-interaction spread model on the same sample used in Table 3: the United States is excluded, the 1995--2023 panel is used, all variables are scaled as in the report, the control vector $$\\mathbf{Z}_{it}$$ is included, country and year fixed effects are included, and robust standard errors are used. From this regression, the script exports $$\\widehat{\\beta}_G$$, $$\\widehat{\\beta}_{GB}$$, $$\\widehat{\\beta}_{GX}$$ and their robust variance-covariance matrix. Panel A evaluates $$-\\partial \\widehat{s}_{it}/\\partial G_{it}=-(\\widehat{\\beta}_G+\\widehat{\\beta}_{GB}B+\\widehat{\\beta}_{GX}X)$$ at the p10, p25, p50, p75, and p90 debt-ratio values, holding vulnerability performance at its sample median. Panel B evaluates the same expression at the p10, p25, p50, p75, and p90 vulnerability-performance values, holding debt/GDP at its sample median. For each plotted point, the standard error is computed by the delta method using the vector $$(1,B_q,X_{median})$$ in Panel A or $$(1,B_{median},X_q)$$ in Panel B. The plotted intervals are point estimates plus or minus 1.96 standard errors, and the two panels use a shared y-axis scale for direct comparison.",
        "",
        "### Table 5. Country Screens Around the Preferred Cutoff",
        "",
        country_theta_screen_tables(),
        "",
        "### Table 6. Debt-Change Regressions",
        "",
        csv_to_md(RESULT / "table6_2_6_3_7_debt_change_regressions.csv"),
        "",
        "### Table 7. Theta-Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_theta_group_heterogeneity.csv"),
        "",
        "### Table 8. Debt-Ratio Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_B_group_heterogeneity.csv"),
        "",
        "### Table 9. Marginal-Relief Grouped Heterogeneity Regressions",
        "",
        compact_group_table(RESULT / "table7_mG_group_heterogeneity.csv"),
        "",
        "### Table 10. Single-Crossing Kink Marginal-Effect Model",
        "",
        "This is not a standard panel threshold model. The kink model directly estimates whether the marginal debt effect of readiness crosses zero at an empirical cutoff.",
        "",
        "$$\\Delta B_{i,t+1}=\\alpha_i+\\tau_t+aG_{it}(c-\\widehat{\\theta}^{F}_{it})_++bG_{it}(\\widehat{\\theta}^{F}_{it}-c)_++\\boldsymbol{\\Gamma}'\\mathbf{Z}_{it}+\\varepsilon_{it}.$$",
        "",
        "$$m(\\theta;c)=a(c-\\theta)_+ + b(\\theta-c)_+.$$",
        "",
        "The theory-implied sign pattern is $$a>0$$ and $$b<0$$: adaptation raises next-period debt below the cutoff but reduces next-period debt above the cutoff.",
        "",
        "This version keeps the two kinked readiness terms but omits $$\\widehat{\\theta}^{F}_{it}$$ and $$(\\widehat{\\theta}^{F}_{it}-c)_+$$ as direct controls.",
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_selected_cutoff_notheta.csv"),
        "",
        csv_to_md_if_exists(RESULT / "table7_deltaB_kink_marginal_effects_notheta.csv"),
        "",
        "##### Figure 3. Continuous Kink Marginal Effect without Theta Controls",
        "",
        "![Figure 3. Continuous kink marginal effect without theta controls](result/figure3_kink_marginal_effect_notheta_continuous.png)",
        "",
        "Notes: The figure plots m(theta;c)=a(c-theta)_+ + b(theta-c)_+ from the single-crossing kink model without theta controls. Positive values imply that readiness improvements are associated with higher next-period debt changes; negative values imply lower next-period debt changes. The vertical dashed line marks the empirical cutoff c.",
        "",
        "Construction details: Figure 3 is generated from the main without-theta-controls single-crossing kink model. The Stata script reads the preferred cutoff from `table7_deltaB_kink_selected_cutoff_notheta.csv`, constructs $$\\Delta B_{i,t+1}=B_{i,t+1}-B_{it}$$, and estimates the kink regression with country fixed effects, year fixed effects, the same control vector $$\\mathbf{Z}_{it}$$, and robust standard errors. The model includes only the two kinked readiness terms, $$G_{it}(c-\\widehat{\\theta}^{F}_{it})_+$$ and $$G_{it}(\\widehat{\\theta}^{F}_{it}-c)_+$$, and deliberately omits $$\\widehat{\\theta}^{F}_{it}$$ and $$(\\widehat{\\theta}^{F}_{it}-c)_+$$ as direct controls. It then takes the p10 and p90 of $$\\widehat{\\theta}^{F}_{it}$$ in the estimation sample and constructs 100 evenly spaced theta values between them. At each grid point, the plotted curve is $$m(\\theta;c)=\\widehat{a}(c-\\theta)_+ + \\widehat{b}(\\theta-c)_+$$. The confidence band is computed by the delta method using the vector $$((c-\\theta)_+, (\\theta-c)_+)$$ and the robust 2-by-2 variance-covariance matrix of $$(\\widehat{a},\\widehat{b})$$. The horizontal dashed line marks zero marginal effect; the vertical dashed line marks the empirical cutoff. The left label identifies the region where the model predicts debt-worsening marginal effects, while the right label identifies the region where the model predicts debt-improving marginal effects.",
        "",
        kink_without_theta_interpretation,
        "",
        "Robustness checks for the without-theta-controls version:",
        "",
        kink_without_theta_robustness,
        "",
        "Full cutoff grids are exported as machine-readable CSV files and are not expanded inline: `table7_deltaB_kink_cutoff_grid*.csv`.",
        "",
        "## 5. Appendix",
        "",
        "### Table A1. Debt-Change Model Control-Set Variants",
        "",
        "The appendix re-estimates the baseline, continuous full-theta, and full-theta dynamics debt-change models under three alternative control sets: $$\\mathbf{Z}_{it}+B_{it}+X_{it}$$, $$B_{it}+X_{it}$$, and no controls. All variants keep country and year fixed effects and robust standard errors.",
        "",
        appendix_debt_control_variants_table(RESULT / "appendix_debt_change_control_variants.csv"),
        "",
        "### Table A2. Single-Crossing Kink without Theta Controls: Control-Set Variants",
        "",
        "These appendix variants keep the main no-theta-controls kink structure but vary the additional controls. The preferred main-text cutoff remains the Z-controls without-theta-controls specification.",
        "",
        kink_without_theta_control_variants,
        "",
        "### Table A3. Single-Crossing Kink with Theta Controls",
        "",
        "This appendix version includes $$\\widehat{\\theta}^{F}_{it}$$ and $$(\\widehat{\\theta}^{F}_{it}-c)_+$$ as direct controls.",
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
        "### Table A4. Single-Crossing Kink with Theta Controls: Control-Set Variants",
        "",
        "These appendix variants keep the direct theta controls and vary the additional controls across $$\\mathbf{Z}_{it}+B_{it}+X_{it}$$, $$B_{it}+X_{it}$$, and no controls.",
        "",
        kink_with_theta_control_variants,
        "",
        "## 6. Result File Inventory",
        "",
        "Large machine-readable support files are saved in `appendixC/result` and are not expanded inline: `theta_full_empirical_panel.csv` and `table7_deltaB_kink_cutoff_grid*.csv`.",
        "",
        md_table(["File", "Bytes", "CSV rows"], inventory),
        "",
        "## 7. Verification",
        "",
        f"- Stata runtime error count from `r(...)`: `{stata_errors}`.",
        f"- Stata completion marker found: `{done}`.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build_report()
