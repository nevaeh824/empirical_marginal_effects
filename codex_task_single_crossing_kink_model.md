# Codex Task: Add a Single-Crossing Segmented Marginal-Effect Model

## 0. Task Summary

Add a new empirical module to the existing Stata and report-generation workflow.

The new module should estimate a **single-crossing segmented marginal-effect model** to test whether the marginal effect of adaptation investment on next-period debt changes from positive to negative as the empirical debt-improving index rises.

This model should **not** be implemented as a standard panel threshold model. The object of interest is not merely whether the coefficient of adaptation differs across two regimes, but whether

\[
\frac{\partial \Delta B_{i,t+1}}{\partial G_{it}}
\]

crosses zero at an empirically estimated cutoff.

---

## 1. Existing Context

The current workflow already constructs the empirical theta index:

\[
\widehat{\theta}^{F}_{it}
=
B_{it}\widehat{m}^{G,F}_{it}
\]

where

\[
\widehat{m}^{G,F}_{it}
=
-\frac{\partial \widehat{s}_{it}}{\partial G_{it}}.
\]

The current debt-change outcome is:

\[
\Delta B_{i,t+1}=B_{i,t+1}-B_{it}.
\]

The existing report already includes:

1. baseline spread regressions;
2. heterogeneity spread regressions;
3. full-interaction empirical theta construction;
4. baseline debt-change regression;
5. continuous full-theta debt regression;
6. grouped heterogeneity regressions;
7. RSS cutoff model.

The new model should be added **after the current Full-Theta RSS Selected Cutoff section**.

---

## 2. Main Goal

Add a model that directly estimates the marginal debt effect of adaptation as a kinked function of empirical theta.

The model should answer:

> Does adaptation investment raise future debt when \(\theta\) is low, but reduce future debt when \(\theta\) is high?

The target marginal effect is:

\[
m(\theta;c)
=
\frac{\partial \Delta B_{i,t+1}}{\partial G_{it}}.
\]

The new empirical cutoff \(c\) should be selected from the data. It should **not** be forced to equal 1.

---

## 3. Input Data

Use the existing output dataset:

```text
best2/result/theta_full_empirical_panel.dta
```

Required variables:

| Variable | Meaning |
|---|---|
| `id` | country identifier |
| `year` | year |
| `debt_ratio` | \(B_{it}\), debt-to-GDP ratio |
| `G_main` | \(G_{it}\), adaptation investment proxy |
| `theta_hat_full` | \(\widehat{\theta}^{F}_{it}\) |
| controls | existing macro controls |

Use the same control vector as the existing debt-change regressions:

\[
Z_{it}
=
\{lnrgdp,\ growth,\ inflation\_cpi,\ OB\_gdp,\ reserves,\ gee,\ rqe,\ tt\}.
\]

Use the same fixed effects as the existing Table 7 debt-change regressions:

\[
\alpha_i+\tau_t.
\]

Use the same baseline sample logic as the existing continuous full-theta debt regression.

---

## 4. Construct the Outcome

Create:

\[
\Delta B_{i,t+1}=B_{i,t+1}-B_{it}.
\]

In code, this should correspond to a variable such as:

```text
B_change
```

using:

```text
F1.debt_ratio - debt_ratio
```

after declaring the panel structure.

---

## 5. New Model Formula

Estimate the following model:

\[
\Delta B_{i,t+1}
=
\alpha_i+\tau_t
+
a\,G_{it}(c-\widehat{\theta}^{F}_{it})_+
+
b\,G_{it}(\widehat{\theta}^{F}_{it}-c)_+
+
\rho_1\widehat{\theta}^{F}_{it}
+
\rho_2(\widehat{\theta}^{F}_{it}-c)_+
+
\Gamma'Z_{it}
+
\varepsilon_{it}.
\]

where

\[
(x)_+=\max(x,0).
\]

The implied marginal effect is:

\[
m(\theta;c)
=
a(c-\theta)_+
+
b(\theta-c)_+.
\]

Therefore:

For \(\theta<c\),

\[
m(\theta;c)=a(c-\theta).
\]

For \(\theta>c\),

\[
m(\theta;c)=b(\theta-c).
\]

The theory-implied sign pattern is:

\[
a>0,\qquad b<0.
\]

Interpretation:

| Region | Marginal effect | Interpretation |
|---|---:|---|
| \(\theta<c\) | \(m(\theta;c)>0\) if \(a>0\) | adaptation raises next-period debt |
| \(\theta>c\) | \(m(\theta;c)<0\) if \(b<0\) | adaptation reduces next-period debt |

---

## 6. Why This Is Not a Standard Threshold Model

Do **not** implement only the following standard threshold model:

\[
\Delta B_{i,t+1}
=
\alpha_i+\tau_t
+
\lambda_LG_{it}\mathbf{1}\{\widehat{\theta}^{F}_{it}<c\}
+
\lambda_HG_{it}\mathbf{1}\{\widehat{\theta}^{F}_{it}\ge c\}
+
\Gamma'Z_{it}
+
\varepsilon_{it}.
\]

That model identifies whether:

\[
\lambda_L\neq \lambda_H.
\]

The new model instead identifies whether:

\[
m(\theta;c)
=
\frac{\partial \Delta B_{i,t+1}}{\partial G_{it}}
\]

crosses zero at an empirical cutoff.

The new model should therefore use:

\[
G_{it}(c-\widehat{\theta}^{F}_{it})_+
\]

and

\[
G_{it}(\widehat{\theta}^{F}_{it}-c)_+
\]

as the two key regressors.

---

## 7. Candidate Cutoff Grid

Generate candidate cutoffs \(c\) from the empirical distribution of:

```text
theta_hat_full
```

in the estimation sample.

Do not allow cutoffs at the extreme tails.

Main trimming rule:

\[
10\% \leq \Pr(\widehat{\theta}^{F}_{it}<c)\leq 90\%.
\]

Robustness trimming rules:

\[
15\%-85\%
\]

and

\[
20\%-80\%.
\]

For each candidate cutoff \(c\), compute:

\[
L_{it}(c)=(c-\widehat{\theta}^{F}_{it})_+
\]

\[
H_{it}(c)=(\widehat{\theta}^{F}_{it}-c)_+
\]

and the two key interaction terms:

\[
G_{it}L_{it}(c)
=
G_{it}(c-\widehat{\theta}^{F}_{it})_+
\]

\[
G_{it}H_{it}(c)
=
G_{it}(\widehat{\theta}^{F}_{it}-c)_+.
\]

Also include the direct theta controls:

\[
\widehat{\theta}^{F}_{it}
\]

and

\[
H_{it}(c).
\]

---

## 8. Estimation for Each Cutoff

For every admissible \(c\), estimate:

\[
\Delta B_{i,t+1}
=
\alpha_i+\tau_t
+
a_cG_{it}L_{it}(c)
+
b_cG_{it}H_{it}(c)
+
\rho_{1c}\widehat{\theta}^{F}_{it}
+
\rho_{2c}H_{it}(c)
+
\Gamma_c'Z_{it}
+
\varepsilon_{it}.
\]

Use the same fixed effects and controls as the existing debt-change regressions.

For each candidate cutoff, store:

| Output | Meaning |
|---|---|
| `cutoff` | candidate \(c\) |
| `rss` | residual sum of squares |
| `N_grid` | sample size |
| `N_low` | observations with \(\theta<c\) |
| `N_high` | observations with \(\theta\ge c\) |
| `share_low` | low-theta share |
| `share_high` | high-theta share |
| `b_low` | estimate of \(a_c\) |
| `se_low` | standard error of \(a_c\) |
| `t_low` | t-statistic of \(a_c\) |
| `p_low` | two-sided p-value of \(a_c\) |
| `b_high` | estimate of \(b_c\) |
| `se_high` | standard error of \(b_c\) |
| `t_high` | t-statistic of \(b_c\) |
| `p_high` | two-sided p-value of \(b_c\) |
| `sign_ok` | equals 1 if \(a_c>0\) and \(b_c<0\) |

---

## 9. Cutoff Selection Rules

Report two cutoff choices.

### 9.1 Main Cutoff: RSS-Minimizing Cutoff

The main cutoff should be:

\[
\widehat c_{RSS}
=
\arg\min_c RSS(c).
\]

This is the primary empirical cutoff.

Do not impose sign restrictions when selecting this cutoff.

After selecting \(\widehat c_{RSS}\), test whether:

\[
\widehat a>0
\]

and

\[
\widehat b<0.
\]

### 9.2 Auxiliary Cutoff: Sign-Consistent RSS Cutoff

Also report an auxiliary cutoff:

\[
\widehat c_{SC}
=
\arg\min_{c:\widehat a_c>0,\ \widehat b_c<0} RSS(c).
\]

Label this clearly as:

```text
sign_consistent_cutoff
```

Do not treat this as the only or primary result, because selecting cutoffs conditional on the desired sign pattern could appear endogenous.

---

## 10. Required Output Files

### 10.1 Full Cutoff Grid

Create:

```text
best2/result/table7_deltaB_kink_cutoff_grid.csv
```

Each row should correspond to one candidate cutoff.

Required columns:

```text
cutoff
rss
N_grid
N_low
N_high
share_low
share_high
b_low
se_low
t_low
p_low
b_high
se_high
t_high
p_high
sign_ok
```

---

### 10.2 Selected Cutoff Table

Create:

```text
best2/result/table7_deltaB_kink_selected_cutoff.csv
```

This file should contain at least two rows:

1. `rss_min_cutoff`
2. `sign_consistent_cutoff`

Required columns:

```text
selection_rule
cutoff
rss
sign_ok
N_model
N_countries
share_low
share_high
b_low
se_low
t_low
p_low
p_low_positive
b_high
se_high
t_high
p_high
p_high_negative
r2
```

Definitions:

\[
p\_low\_positive
\]

is the one-sided p-value for:

\[
H_1:a>0.
\]

\[
p\_high\_negative
\]

is the one-sided p-value for:

\[
H_1:b<0.
\]

---

### 10.3 Marginal Effect Table

Create:

```text
best2/result/table7_deltaB_kink_marginal_effects.csv
```

Using \(\widehat c_{RSS}\), compute:

\[
m(\theta;\widehat c_{RSS})
=
\widehat a(\widehat c_{RSS}-\theta)_+
+
\widehat b(\theta-\widehat c_{RSS})_+.
\]

Evaluate this at the following empirical theta quantiles:

\[
p10,\quad p25,\quad p50,\quad p75,\quad p90.
\]

Required columns:

```text
theta_quantile
theta_point
marginal_effect
standard_error
t_stat
p_value
```

If standard errors are not yet implemented, output point estimates first and mark standard error fields as missing. Prefer delta-method or bootstrap standard errors if feasible.

---

## 11. Robustness Outputs

Create robustness versions using the same model and naming conventions.

### 11.1 Alternative Trimming Rules

Create versions for:

\[
15\%-85\%
\]

and

\[
20\%-80\%.
\]

Suggested suffixes:

```text
_trim15
_trim20
```

Example:

```text
table7_deltaB_kink_selected_cutoff_trim15.csv
```

---

### 11.2 Country-Clustered Standard Errors

Create a version with standard errors clustered by country.

Suggested suffix:

```text
_cluster
```

Example:

```text
table7_deltaB_kink_selected_cutoff_cluster.csv
```

---

### 11.3 Lagged Theta

Create a version using:

\[
\widehat{\theta}^{F}_{i,t-1}
\]

instead of contemporaneous \(\widehat{\theta}^{F}_{it}\).

Suggested suffix:

```text
_lagtheta
```

Example:

```text
table7_deltaB_kink_selected_cutoff_lagtheta.csv
```

---

### 11.4 Longer Debt Horizons

Create versions for:

\[
\Delta B_{i,t+2}=B_{i,t+2}-B_{it}
\]

and

\[
\Delta B_{i,t+3}=B_{i,t+3}-B_{it}.
\]

Suggested suffixes:

```text
_h2
_h3
```

Example:

```text
table7_deltaB_kink_selected_cutoff_h2.csv
```

---

## 12. Report Generator Updates

Update:

```text
best2/generate_best2_report.py
```

so that the markdown report includes a new section after the existing Full-Theta RSS Selected Cutoff section.

Suggested section title:

```text
### Single-Crossing Kink Marginal-Effect Model
```

Add the model formula:

\[
\Delta B_{i,t+1}
=
\alpha_i+\tau_t
+
aG_{it}(c-\widehat{\theta}^{F}_{it})_+
+
bG_{it}(\widehat{\theta}^{F}_{it}-c)_+
+
\rho_1\widehat{\theta}^{F}_{it}
+
\rho_2(\widehat{\theta}^{F}_{it}-c)_+
+
\Gamma'Z_{it}
+
\varepsilon_{it}.
\]

Add the marginal effect formula:

\[
m(\theta;c)=a(c-\theta)_+ + b(\theta-c)_+.
\]

Add the interpretation:

\[
a>0,\quad b<0
\]

means that adaptation raises next-period debt below the cutoff but reduces next-period debt above the cutoff.

Add the following tables:

1. `table7_deltaB_kink_selected_cutoff.csv`
2. `table7_deltaB_kink_marginal_effects.csv`
3. optional appendix table: `table7_deltaB_kink_cutoff_grid.csv`

---

## 13. Interpretation Rules

### Case 1: Strong Support

If at \(\widehat c_{RSS}\):

\[
\widehat a>0
\]

and

\[
\widehat b<0,
\]

and both are statistically meaningful, write:

> The segmented marginal-effect model identifies an empirical zero-crossing pattern. Below the cutoff, adaptation investment raises next-period debt; above the cutoff, adaptation investment reduces next-period debt. This supports the interpretation of \(\widehat{\theta}^{F}_{it}\) as a debt-improving capacity index.

---

### Case 2: Only Low-Theta Effect Is Supported

If:

\[
\widehat a>0
\]

but

\[
\widehat b<0
\]

is weak or insignificant, write:

> The evidence supports a debt-worsening effect of adaptation in the low-theta region, but the debt-improving effect in the high-theta region is weaker.

---

### Case 3: Only High-Theta Effect Is Supported

If:

\[
\widehat b<0
\]

but

\[
\widehat a>0
\]

is weak or insignificant, write:

> The evidence supports a debt-improving effect of adaptation in the high-theta region, but the debt-worsening effect in the low-theta region is weaker.

---

### Case 4: No Sign Support

If the signs do not satisfy:

\[
\widehat a>0,\qquad \widehat b<0,
\]

write:

> The current data do not support the single-crossing segmented marginal-effect specification.

Do not claim that the model supports the theory if the sign pattern fails.

---

## 14. Acceptance Checklist

The task is complete only if all of the following are true:

- [ ] The Stata workflow runs without errors.
- [ ] The original results are preserved.
- [ ] The new model is added after the existing RSS cutoff model.
- [ ] The model uses \(G_{it}(c-\theta)_+\) and \(G_{it}(\theta-c)_+\), not only threshold dummies.
- [ ] The cutoff grid excludes extreme tails.
- [ ] The main cutoff is selected by minimum RSS without sign restriction.
- [ ] The sign-consistent cutoff is reported separately.
- [ ] The selected-cutoff table is exported.
- [ ] The full cutoff-grid table is exported.
- [ ] The marginal-effect table is exported.
- [ ] The report generator includes the new formulas and tables.
- [ ] The report clearly distinguishes this model from a standard panel threshold model.
- [ ] Interpretation is conditional on the actual estimated signs of \(a\) and \(b\).

---

## 15. Preferred Terminology

Use one of the following names:

```text
Single-crossing segmented marginal-effect model
```

or

```text
Kinked marginal-effect model
```

Avoid calling it:

```text
Panel threshold model
```

because the goal is not merely to test coefficient differences across regimes, but to estimate a zero-crossing marginal effect.
