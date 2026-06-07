# Empirical Marginal Effects Workflow

本文档梳理当前文件夹 `c:\Users\chenyu\Desktop\0606` 的完整工作流。核心实证流水线位于 `best2/`，围绕固定指标组合 `readiness_delta100__vulnerability_delta100` 生成回归表、theta 面板、三张图和最终 markdown 报告。

## 1. 文件夹角色

| 路径 | 类型 | 作用 |
| --- | --- | --- |
| `cleaned_imf_like_panel_1995_2023.csv` | 原始输入数据 | 1995-2023 年国家面板，是 Stata 实证脚本的唯一主数据入口。 |
| `best2/paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do` | Stata 主入口 | 清洗变量、构造交互项、估计所有表格模型、生成 theta 面板、导出图 2 和图 3 的绘图数据。 |
| `best2/plot_figure1_theta_distribution.py` | Python 绘图脚本 | 使用 theta 面板和 preferred cutoff 绘制 Figure 1。 |
| `best2/plot_figure2_spread_relief.py` | Python 绘图脚本 | 使用 Stata 导出的 Table 3 full-interaction 边际效应数据绘制 Figure 2。 |
| `best2/plot_figure3_kink_curve.py` | Python 绘图脚本 | 使用 Stata 导出的 no-theta kink 曲线数据绘制 Figure 3。 |
| `best2/generate_best2_report.py` | Python 报告生成器 | 读取 `best2/result/` 中的 CSV/TEX/图片文件，生成最终报告。 |
| `best2/best2_readiness_delta_vulnerability_delta_report.md` | 最终报告 | 当前主要阅读文件，包含公式、表格、图、解释和结果文件清单。 |
| `best2/result/` | 生成结果目录 | 保存 Stata/Python 生成的 `.csv`、`.dta`、`.tex`、`.png`、`.pdf`、`.svg`、`.log`。 |
| `codex_task_single_crossing_kink_model.md` | 任务规格 | single-crossing kink marginal-effect model 的原始实现要求。 |
| `ndgain_scores_explainer.md` | 指标说明 | 解释 ND-GAIN vulnerability/readiness 及 delta 指标的含义。 |
| `empirical_section_sovereign_debt_best2_indicator_conclusion.tex` 和 PDF | 论文段落材料 | 与实证结果相关的论文写作材料。 |
| `ManagingClimateRisk_*.pdf` | 理论参考 | 债务、风险和最优适应投资相关理论参考。 |

## 2. 总体依赖关系

```text
cleaned_imf_like_panel_1995_2023.csv
        |
        v
best2/paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do
        |
        |-- table1/table2/table3/table6/table7 CSV, DTA, TEX
        |-- theta_full_empirical_panel.csv/.dta
        |-- figure2_spread_relief_marginal_effects.csv
        |-- figure2_table3_fullinteraction_coefficients.csv
        |-- figure3_kink_marginal_effect_notheta_continuous.csv/.dta
        |-- figure3_kink_marginal_effect_notheta_coefficients.csv
        |-- appendix_debt_change_control_variants.csv/.dta
        |-- appendix kink control-set variants:
        |   table7_deltaB_kink_*_notheta_zbx/bx/none
        |   table7_deltaB_kink_*_withtheta_zbx/bx/none
        v
best2/result/
        |
        |-- plot_figure1_theta_distribution.py  -> figure1_theta_distribution_cutoff.png/pdf/svg
        |-- plot_figure2_spread_relief.py       -> figure2.png/pdf
        |-- plot_figure3_kink_curve.py          -> figure3_kink_marginal_effect_notheta_continuous.png/pdf
        v
best2/generate_best2_report.py
        |
        v
best2/best2_readiness_delta_vulnerability_delta_report.md
```

原则上，修改 Stata 模型或样本设定后，需要重新运行 Stata，再重新运行三张图和报告生成器。只修改报告文字模板时，通常只需要重新运行 `generate_best2_report.py`。

## 3. 运行环境

需要：

- Stata 18，当前命令示例使用 `C:\Environment_tools\Stata18\StataMP-64.exe`。
- Python 3。
- Python 包：`pandas`、`numpy`、`matplotlib`。

Stata 脚本目前主要使用 Stata 自带 `regress ..., vce(robust)`、国家固定效应和年份固定效应虚拟变量；不依赖 `reghdfe`。

## 4. 一键复现顺序

从项目根目录 `c:\Users\chenyu\Desktop\0606` 运行：

```powershell
& 'C:\Environment_tools\Stata18\StataMP-64.exe' /e do 'best2\paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do' 'C:\Users\chenyu\Desktop\0606'
python best2\plot_figure1_theta_distribution.py
python best2\plot_figure2_spread_relief.py
python best2\plot_figure3_kink_curve.py
python best2\generate_best2_report.py
```

注意：Stata `/e` 模式可能会启动后台进程并立即返回 shell。确认 Stata 完成后再运行 Python 脚本，最稳妥的检查方式是查看 `best2/result/paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.log` 末尾是否出现：

```text
Done. Retained Paper B outputs written to ...
```

## 5. Stata 主流程

Stata 主入口是：

```text
best2/paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.do
```

### 5.1 路径与固定指标

do-file 开头通过参数 `project_root` 定位项目根目录。如果没有传入参数，则使用当前工作目录。核心全局变量是：

```stata
global newdata "${empirical_dir}/cleaned_imf_like_panel_1995_2023.csv"
global g_source "readiness_delta100"
global x_source "vulnerability_delta100"
global combo_id "readiness_delta100__vulnerability_delta100"
global best_dir "${empirical_dir}/best2"
global out "${best_dir}/result"
```

因此，当前 best2 结果固定对应：

```text
G = readiness_delta100
X = vulnerability_delta100
```

### 5.2 变量预处理

`prep_panel` 是共享预处理程序。它完成：

- `encode iso3, gen(id)` 并 `xtset id year`。
- 标记并在估计中排除 United States。
- 将核心变量缩放为 0.01 倍：
  - `s = 0.01 * bond_spreads`
  - `G = 0.01 * readiness_delta100`
  - `X = 0.01 * vulnerability_delta100`
  - `B = 0.01 * debt_gdp`
  - `Z = {lnrgdp, growth, inflation_cpi, OB_gdp, reserves, gee, rqe, tt}` 中每个控制变量也乘以 0.01。
- 构造交互项：
  - `G_B = G_main * debt_ratio`
  - `G_X = G_main * X_main`
  - `G_E = G_main * exposure100`
  - `G_z = G_main * z` for each control in `Z`。

### 5.3 Table 1 Post-Preprocessing Descriptive Statistics

Table 1 使用 `prep_panel` 完成缩放和变量构造后的 non-U.S. 1995--2023 panel。每个变量按自身非缺失样本计算 `N`、mean、SD、median、min 和 max。

变量覆盖：

- `S`: `s_it = 0.01 * bond_spreads`
- `G`: `G_it = 0.01 * readiness_delta100`
- `B`: `B_it = 0.01 * debt_gdp`
- `X`: `X_it = 0.01 * vulnerability_delta100`
- `Z`: `lnrgdp`、`growth`、`inflation_cpi`、`OB_gdp`、`reserves`、`gee`、`rqe`、`tt`，均已乘以 0.01

主要输出：

```text
best2/result/table1_preprocessed_descriptive_stats.csv
best2/result/table1_preprocessed_descriptive_stats.dta
best2/result/table1_preprocessed_descriptive_stats.tex
```

该表用于报告中的 Table 1。

### 5.4 Table 2 Baseline Spread Model

样本：

- 排除 United States。
- 年份为 1995-2023。
- 国家固定效应和年份固定效应。
- robust standard errors。

主要输出：

```text
best2/result/table2_baseline_fe_periods.tex
```

该表用于报告中的 Table 2。

### 5.5 Table 3 Heterogeneity and Full-Interaction Spread Models

估计三类 spread regression：

- Debt heterogeneity：加入 `G_it x B_it`。
- Climate-risk heterogeneity：加入 `G_it x X_it`。
- Full interaction：同时加入 `G_it x B_it` 和 `G_it x X_it`。

报告中还合并展示 full interaction + `G_it x Z_it` 的结果。

主要输出：

```text
best2/result/table3_heterogeneity_theta.tex
best2/result/table6_fullinteraction_theta_regression.tex
```

Figure 2 的绘图数据也在这一段生成：

```text
best2/result/figure2_table3_fullinteraction_coefficients.csv
best2/result/figure2_spread_relief_marginal_effects.csv
```

其中 `figure2_spread_relief_marginal_effects.csv` 已经包含 p10/p25/p50/p75/p90 网格、点估计、delta-method standard errors 和 95% confidence intervals。

### 5.6 Full-Interaction Empirical Theta

full-interaction theta 使用如下边际效应：

```text
d s_it / d G_it
  = beta_G
  + beta_GB * B_it
  + beta_GX * X_it
  + Gamma_GZ' Z_it
```

并定义：

```text
mG_hat_full = - d s_it / d G_it
theta_hat_full = B_it * mG_hat_full
```

主要输出：

```text
best2/result/theta_full_empirical_panel.csv
best2/result/theta_full_empirical_panel.dta
best2/result/table6_theta_descriptive_stats.csv
best2/result/table6_theta_descriptive_stats.tex
```

`theta_full_empirical_panel.csv` 是后续 Figure 1、country screen、debt-change regressions、kink model 的关键中间数据。

### 5.7 Debt-Change Models

债务变化变量定义为：

```text
Delta B_{i,t+1} = B_{i,t+1} - B_{it}
```

相关输出包括：

```text
best2/result/table6_2_debt_level_dynamics_regression.csv
best2/result/table7_0_baseline_debt_change_regression.csv
best2/result/table7_continuous_theta_debt_regression.csv
best2/result/table6_2_6_3_7_debt_change_regressions.csv
best2/result/appendix_debt_change_control_variants.csv
```

这些文件分别对应 full-theta debt-level dynamics、baseline debt-change regression、continuous full-theta debt regression 和合并债务变化表。

`appendix_debt_change_control_variants.csv` 是附录专用结果。它对三类 debt-change 模型都额外估计三种控制组合：

- `Z+B+X`：控制宏观/制度控制向量 `Z`、当前债务水平 `B` 和 vulnerability performance `X`。
- `B+X`：只控制当前债务水平 `B` 和 vulnerability performance `X`。
- `None`：除国家固定效应和年份固定效应外，不加入额外控制变量。

### 5.8 Grouped Heterogeneity Regressions

Stata 脚本基于 `theta_full_empirical_panel.dta` 生成三类分组回归：

```text
best2/result/table7_theta_group_heterogeneity.csv
best2/result/table7_B_group_heterogeneity.csv
best2/result/table7_mG_group_heterogeneity.csv
```

分组维度分别是：

- `theta_hat_full` 分位组。
- `debt_ratio` 分位组。
- `mG_hat_full` 分位组。

报告中展示的是压缩后的 markdown 表。

### 5.9 Single-Crossing Kink Marginal-Effect Models

核心程序是 `run_deltaB_kink`。它在候选 cutoff 网格上估计：

```text
Delta B_{i,t+1}
  = country FE + year FE
  + a * G_it * max(c - theta_hat_full, 0)
  + b * G_it * max(theta_hat_full - c, 0)
  + controls
  + error
```

当前保留两个版本：

1. With Theta Controls：额外加入 `theta_hat_full` 和 `max(theta_hat_full - c, 0)` 作为直接控制。
2. Without Theta Controls：不加入上述两个直接 theta 控制，是当前主结果版本。

`run_deltaB_kink` 现在还支持 `controlset()` 参数：

- `controlset("z")`：默认设定，控制 `Z`，用于主文 preferred no-theta 结果和原有 robustness。
- `controlset("zbx")`：控制 `Z+B+X`，用于 appendix control-set variants。
- `controlset("bx")`：控制 `B+X`，用于 appendix control-set variants。
- `controlset("none")`：不加入额外控制变量，仍保留国家固定效应和年份固定效应，用于 appendix control-set variants。

主结果 cutoff 来自 without-theta-controls 版本：

```text
best2/result/table7_deltaB_kink_selected_cutoff_notheta.csv
```

主结果的边际效应表为：

```text
best2/result/table7_deltaB_kink_marginal_effects_notheta.csv
```

完整 cutoff grid 输出包括：

```text
best2/result/table7_deltaB_kink_cutoff_grid*.csv
```

robustness 版本包括：

- `_trim15`
- `_trim20`
- `_cluster`
- `_lagtheta`
- `_h2`
- `_h3`

每个 robustness 版本通常都有：

```text
table7_deltaB_kink_cutoff_grid_SUFFIX.csv
table7_deltaB_kink_selected_cutoff_SUFFIX.csv
table7_deltaB_kink_marginal_effects_SUFFIX.csv
```

appendix 控制组合版本使用以下 suffix：

```text
_notheta_zbx
_notheta_bx
_notheta_none
_withtheta_zbx
_withtheta_bx
_withtheta_none
```

其中 `_notheta_*` 是不含直接 theta controls 的 kink 版本，`_withtheta_*` 是包含 `theta_hat_full` 与 `max(theta_hat_full - c, 0)` 直接控制的 kink 版本。主文仍使用 `_notheta` 的默认 Z-controls RSS-minimizing cutoff 作为 preferred cutoff；with-theta-controls 结果只在 appendix 展示。

### 5.10 Figure 3 数据导出

`export_fig3_kink_curve` 在 Stata 侧重新读取 no-theta preferred cutoff，估计 no-theta kink model，并输出连续曲线数据：

```text
best2/result/figure3_kink_marginal_effect_notheta_coefficients.csv
best2/result/figure3_kink_marginal_effect_notheta_continuous.csv
best2/result/figure3_kink_marginal_effect_notheta_continuous.dta
```

Python 只负责将这些 Stata 计算好的曲线点画成图。

## 6. 三张图的生成流程

### 6.1 Figure 1: Theta Distribution and Country Ranking

脚本：

```text
best2/plot_figure1_theta_distribution.py
```

输入：

```text
best2/result/theta_full_empirical_panel.csv
best2/result/table7_deltaB_kink_selected_cutoff_notheta.csv
```

处理逻辑：

- 保留 `theta_sample_full == 1` 且 `theta_hat_full` 非缺失的 country-year observations。
- 左图：绘制 `theta_hat_full` 的 country-year 分布，包含 histogram 和 kernel-density overlay。
- 右图：按国家聚合 `theta_hat_full` 的样本均值，并从低到高排序。
- 两个 panel 都使用 without-theta-controls kink model 的 preferred cutoff 作为虚线阈值。

输出：

```text
best2/result/figure1_theta_distribution_cutoff.png
best2/result/figure1_theta_distribution_cutoff.pdf
best2/result/figure1_theta_distribution_cutoff.svg
best2/result/figure1_country_theta_ranking.csv
```

### 6.2 Figure 2: Marginal Spread Relief from Table 3 Full Interaction

Stata 输入逻辑：

- 使用 Table 3 full-interaction spread model。
- 排除 United States。
- 使用 1995-2023。
- 使用同样缩放变量、控制变量、国家固定效应、年份固定效应和 robust standard errors。

Stata 先导出：

```text
best2/result/figure2_spread_relief_marginal_effects.csv
best2/result/figure2_table3_fullinteraction_coefficients.csv
```

Python 脚本：

```text
best2/plot_figure2_spread_relief.py
```

处理逻辑：

- Panel A：在 Debt/GDP 的 p10、p25、p50、p75、p90 上评价 spread relief，固定 `vulnerability_delta` 为样本中位数。
- Panel B：在 `vulnerability_delta` 的 p10、p25、p50、p75、p90 上评价 spread relief，固定 Debt/GDP 为样本中位数。
- 点估计为：

```text
Relief = - (beta_G + beta_GB * B + beta_GX * X)
```

- 置信区间由 Stata 侧 delta method 计算。
- 两个 panel 使用共同 y 轴以便比较量级。

输出：

```text
best2/result/figure2.png
best2/result/figure2.pdf
```

### 6.3 Figure 3: Continuous Kink Marginal Effect without Theta Controls

Stata 输入逻辑：

- 使用 without-theta-controls single-crossing kink model。
- cutoff 来自 `table7_deltaB_kink_selected_cutoff_notheta.csv`。
- 重新估计 no-theta kink regression。
- 在估计样本的 `theta_hat_full` p10 到 p90 之间生成 100 个网格点。
- 对每个网格点计算：

```text
m(theta; c) = a * (c - theta)_+ + b * (theta - c)_+
```

- 使用 `(a, b)` 的 robust 2-by-2 variance-covariance matrix 做 delta-method confidence band。

Stata 输出：

```text
best2/result/figure3_kink_marginal_effect_notheta_coefficients.csv
best2/result/figure3_kink_marginal_effect_notheta_continuous.csv
best2/result/figure3_kink_marginal_effect_notheta_continuous.dta
```

Python 脚本：

```text
best2/plot_figure3_kink_curve.py
```

Python 输出：

```text
best2/result/figure3_kink_marginal_effect_notheta_continuous.png
best2/result/figure3_kink_marginal_effect_notheta_continuous.pdf
```

## 7. 报告生成流程

报告生成器：

```text
best2/generate_best2_report.py
```

输入包括：

- `table1_preprocessed_descriptive_stats.csv`
- `table2_baseline_fe_periods.tex`
- `table3_heterogeneity_theta.tex`
- `table6_fullinteraction_theta_regression.tex`
- `table6_theta_descriptive_stats.csv`
- `table6_2_debt_level_dynamics_regression.csv`
- `table7_0_baseline_debt_change_regression.csv`
- `table7_continuous_theta_debt_regression.csv`
- `table6_2_6_3_7_debt_change_regressions.csv`
- `appendix_debt_change_control_variants.csv`
- `table7_*_heterogeneity.csv`
- `table7_deltaB_kink_selected_cutoff*.csv`
- `table7_deltaB_kink_marginal_effects*.csv`
- 三张图的 `.png` 文件。
- Stata log 文件。

生成逻辑：

- 从 `.tex` 回归表中解析系数、t-statistics、样本量、国家数和 adjusted R2。
- 从 `.csv` 结果文件中直接转为 markdown 表。
- 重新计算 country screen 表：
  - 债务低于样本国家中位数、theta 始终高于 cutoff、`mG_hat_full` 位于顶端四分位。
  - 债务高于样本国家中位数、theta 始终低于 cutoff、`mG_hat_full` 位于底部四分位。
- 嵌入 Figure 1、Figure 2、Figure 3。
- 生成 Appendix A1--A4：
  - A1 展示三类 debt-change 模型的 `Z+B+X`、`B+X`、`None` 控制组合。
  - A2 展示 without-theta-controls kink model 的三种控制组合。
  - A3 展示 with-theta-controls kink model 的 selected cutoff、marginal effects 和 robustness。
  - A4 展示 with-theta-controls kink model 的三种控制组合。
- 在报告末尾生成 `best2/result/` 文件清单。
- 检查 Stata log 中是否有 `r(...)` runtime error 和完成标记。

输出：

```text
best2/best2_readiness_delta_vulnerability_delta_report.md
```

重要约定：不要长期手工改最终报告正文。若修改会被复用，应修改 `generate_best2_report.py`，然后重新生成报告。

## 8. 结果文件命名规则

`best2/result/` 中常见文件可以按前缀识别：

| 前缀 | 含义 |
| --- | --- |
| `table1_` | post-preprocessing descriptive statistics for `S/G/B/X/Z`。 |
| `table2_` | baseline spread fixed-effects estimates。 |
| `table3_` | spread heterogeneity and full-interaction estimates。 |
| `table6_` | empirical theta、theta descriptive stats、full-theta debt-level dynamics。 |
| `table7_` | debt-change regressions、grouped heterogeneity、single-crossing kink models。 |
| `appendix_` | appendix-only support files, currently debt-change control-set variants。 |
| `theta_full_empirical_panel` | full-interaction empirical theta 面板，是后续 debt/kink/figure 的关键中间数据。 |
| `figure1_` | Figure 1 输出和 country ranking。 |
| `figure2_` | Figure 2 绘图输入和输出。 |
| `figure3_` | Figure 3 绘图输入和输出。 |
| `paperB_*.log` | Stata 主脚本运行日志。 |

同一结果通常同时有 `.csv`、`.dta` 和 `.tex`：

- `.csv`：给 Python 报告生成器和人工检查使用。
- `.dta`：给 Stata 后续步骤和复查使用。
- `.tex`：给论文 LaTeX 表格使用。

## 9. 常见修改点

### 9.1 修改 G/X 指标组合

改 Stata do-file 开头：

```stata
global g_source "readiness_delta100"
global x_source "vulnerability_delta100"
global combo_id "readiness_delta100__vulnerability_delta100"
```

修改后必须重新运行 Stata、三张图和报告生成器。

### 9.2 修改样本期或排除国家

样本期目前在多个表格段落中使用：

```stata
local ifperiod "year >= 1995 & year <= 2023"
```

United States 排除逻辑在 `prep_panel` 中生成 `is_us`，估计时使用 `is_us == 0`。修改样本规则后必须重新运行完整流程。

### 9.3 修改控制变量

控制变量集中定义在：

```stata
global ctrls "lnrgdp growth inflation_cpi OB_gdp reserves gee rqe tt"
global ctrls_miss "lnrgdp, growth, inflation_cpi, OB_gdp, reserves, gee, rqe, tt"
global gctrls "G_lnrgdp G_growth G_inflation_cpi G_OB_gdp G_reserves G_gee G_rqe G_tt"
global gctrls_miss "G_lnrgdp, G_growth, G_inflation_cpi, G_OB_gdp, G_reserves, G_gee, G_rqe, G_tt"
```

如果新增或删除控制变量，需要同步更新：

- `global ctrls`
- `global ctrls_miss`
- `global gctrls`
- `global gctrls_miss`
- `prep_panel` 中生成 `G_z` 的循环。
- 报告中公式或文字说明。

### 9.4 修改 kink cutoff 选择规则

主 cutoff 目前使用 without-theta-controls 模型的 RSS-minimizing cutoff：

```text
best2/result/table7_deltaB_kink_selected_cutoff_notheta.csv
```

Figure 1 和 Figure 3 都读取这个 preferred cutoff。若更改主 cutoff 规则，需要同步检查：

- Stata `run_deltaB_kink` 的 cutoff selection 逻辑。
- `plot_figure1_theta_distribution.py` 的 `CUTOFF_PATH`。
- `export_fig3_kink_curve` 中读取的 selected cutoff 文件。
- `generate_best2_report.py` 中相关文字解释。

### 9.5 修改图形风格或输出文件名

图形风格在三个 Python 脚本中分别控制。若只改颜色、标题、注释或输出文件名，通常只需重新运行对应绘图脚本和报告生成器。

如果改 Figure 2 或 Figure 3 的估计逻辑，应先改 Stata do-file 导出的绘图数据，再运行 Python。

## 10. 验证清单

Stata 后检查：

```powershell
rg "^r\([0-9]+\);" best2\result\paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.log
rg "Done\. Retained Paper B outputs" best2\result\paperB_best2_readiness_delta_vulnerability_delta_1995_2023_tables.log
```

Python 语法检查：

```powershell
python -m py_compile best2\generate_best2_report.py
python -m py_compile best2\plot_figure1_theta_distribution.py
python -m py_compile best2\plot_figure2_spread_relief.py
python -m py_compile best2\plot_figure3_kink_curve.py
```

核心输出是否存在：

```powershell
Test-Path best2\result\theta_full_empirical_panel.csv
Test-Path best2\result\table1_preprocessed_descriptive_stats.csv
Test-Path best2\result\table7_deltaB_kink_selected_cutoff_notheta.csv
Test-Path best2\result\appendix_debt_change_control_variants.csv
Test-Path best2\result\table7_deltaB_kink_selected_cutoff_notheta_zbx.csv
Test-Path best2\result\table7_deltaB_kink_selected_cutoff_withtheta_zbx.csv
Test-Path best2\result\figure1_theta_distribution_cutoff.png
Test-Path best2\result\figure2.png
Test-Path best2\result\figure3_kink_marginal_effect_notheta_continuous.png
Test-Path best2\best2_readiness_delta_vulnerability_delta_report.md
```

## 11. Git 工作流建议

本项目当前已经初始化 git。推荐提交时至少包括：

- 源代码：`best2/*.do`、`best2/*.py`、`WORKFLOW.md`、`README.md`、任务/说明 markdown。
- 最终阅读成果：`best2/best2_readiness_delta_vulnerability_delta_report.md`。
- 关键图像：`best2/result/figure*.png` 和必要 PDF。
- 关键机器可读结果：如果希望 GitHub 上完整复现报告，应提交报告所依赖的 CSV/TEX；若只希望提交代码和最终报告，可减少提交 `best2/result/*.dta` 等大文件。

提交前建议运行：

```powershell
git status --short
```

确认哪些是手工代码修改，哪些是 Stata/Python 生成结果，再决定是否全部纳入版本控制。
