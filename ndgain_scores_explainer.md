# ND-GAIN 指标说明：`vulnerability`、`readiness`、`vulnerability_delta`、`readiness_delta`

本文根据 **University of Notre Dame Global Adaptation Initiative (ND-GAIN) Country Index Technical Report, Updated August 26, 2024** 与 ND-GAIN 官方 Methodology / Download Data 页面整理。适用于理解 ND-GAIN 数据集中常见字段：`vulnerability`、`readiness`、`vulnerability_delta`、`readiness_delta`，以及它们的子指标含义、构建方式和数据来源。

---

## 1. 四个核心分数的含义

### 1.1 `vulnerability`

`vulnerability` 是国家对气候变化负面影响的脆弱性分数。ND-GAIN 将 vulnerability 定义为：人类社会受到气候灾害负面影响的倾向或预置状态。

官方框架中，`vulnerability` 由 **6 个生命支持部门**构成：

1. Food 食物
2. Water 水
3. Health 健康
4. Ecosystem Services 生态系统服务
5. Human Habitat 人居
6. Infrastructure 基础设施

每个部门有 6 个指标：

- 2 个 `Exposure` 指标
- 2 个 `Sensitivity` 指标
- 2 个 `Adaptive Capacity` 指标

因此，`vulnerability` 一共有 **36 个底层指标**。

**分数方向：**

- 取值通常在 0–1。
- **越高 = 越脆弱 = 越差。**
- **越低 = 越不脆弱 = 越好。**

### 1.2 `readiness`

`readiness` 是国家利用投资并将其转化为气候适应行动的能力。ND-GAIN 将 readiness 定义为：一个国家是否具备安全、高效的商业环境，从而有效使用公共和私人部门投资来开展适应行动。

官方框架中，`readiness` 由 **3 个组成部分**构成：

1. Economic Readiness 经济准备度
2. Governance Readiness 治理准备度
3. Social Readiness 社会准备度

一共有 **9 个 readiness 指标**：

- Economic Readiness：1 个指标，即 Doing Business
- Governance Readiness：4 个指标
- Social Readiness：4 个指标

**分数方向：**

- 取值通常在 0–1。
- **越高 = 越有准备度 = 越好。**
- **越低 = 越缺乏准备度 = 越差。**

### 1.3 `readiness_delta`

`readiness_delta` 可理解为 **GDP-adjusted readiness score**，即扣除 GDP per capita 影响后的 readiness 相对表现。

官方 Methodology 说明，ND-GAIN 分数与 GDP per capita 存在线性相关，因此官方用每一年 GDP per capita 与对应分数之间的线性关系来构造 GDP-adjusted score。其核心含义是：

> 一个国家的实际 readiness 分数，相对于其 GDP per capita 所预测的 readiness 分数，高出或低出多少。

可写成近似公式：

```text
readiness_delta_it = readiness_it - E(readiness_it | GDP per capita_it, year_t)
```

**解读：**

- `readiness_delta > 0`：readiness 高于同等 GDP 水平下的预期，表现好于经济发展水平所暗示的水平。
- `readiness_delta = 0`：readiness 大致符合 GDP 水平预期。
- `readiness_delta < 0`：readiness 低于同等 GDP 水平下的预期。

### 1.4 `vulnerability_delta`

`vulnerability_delta` 可理解为 **GDP-adjusted vulnerability score**，即扣除 GDP per capita 影响后的 vulnerability 相对表现。

由于 vulnerability 本身是“越低越好”，官方 Methodology 特别说明：对于 GDP-adjusted Vulnerability，**正值表示该国 vulnerability 低于其 GDP 水平所预期的 vulnerability**，也就是表现更好。

因此可写成方向一致的近似公式：

```text
vulnerability_delta_it = E(vulnerability_it | GDP per capita_it, year_t) - vulnerability_it
```

**解读：**

- `vulnerability_delta > 0`：实际 vulnerability 低于同等 GDP 水平下的预期，表现更好。
- `vulnerability_delta = 0`：vulnerability 大致符合 GDP 水平预期。
- `vulnerability_delta < 0`：实际 vulnerability 高于同等 GDP 水平下的预期，表现更差。

> 注意：`readiness_delta` 和 `vulnerability_delta` 不是 readiness / vulnerability 的原始水平，而是相对 GDP 预期值的偏离。它们适合回答“一个国家相对于其经济发展水平表现得好不好”，而不是回答“这个国家绝对有多脆弱或多有准备度”。

---

## 2. ND-GAIN 分数的通用构建方式

ND-GAIN 将原始数据转换为可比较的 0–1 分数，核心步骤如下。

### 2.1 原始数据与指标来源

官方技术报告说明，ND-GAIN 的 45 个核心指标来自 74 个数据源，提供 74 个底层数据。其中：

- 20 个指标直接来自数据源；
- 25 个指标由多个底层数据计算合成。

官方 Download Data 页面说明，下载包中通常包含：

- `raw.csv`：原始数据，来自公开数据源；
- `input.csv`：插值后用于计算的输入数据；
- `score.csv`：缩放到 0–1 后用于聚合的指标分数。

### 2.2 缺失值处理

- 如果某个国家某些年份缺失，ND-GAIN 使用线性插值。
- 如果某国某指标完全没有数据，则该指标记为 missing，不参与该国对应平均值的计算。

### 2.3 Reference point 与 baseline range

ND-GAIN 采用 “proximity-to-reference point / proximity-to-goalpost” 思路。Reference point 表示理想状态：

- 对 vulnerability 指标，理想状态是 **zero vulnerability**；
- 对 readiness 指标，理想状态是 **full readiness**。

Reference point 的来源包括：

1. 观测数据的 baseline minimum 或 maximum；
2. 基于适应或发展实践的逻辑目标值，例如儿童营养不良为 0%、可靠饮水为 100%；
3. 数据源自带的目标值或满分，例如某些 1–5 评分指标的满分。

### 2.4 0–1 缩放公式

技术报告给出的缩放公式为：

```text
score = | direction - (raw data - reference point) / (baseline maximum - baseline minimum) |
```

其中：

- vulnerability 指标：`direction = 0`
- readiness 指标：`direction = 1`

因此：

- vulnerability 类指标的分数越高，表示距离“零脆弱性”越远，越差；
- readiness 类指标的分数越高，表示越接近“完全准备好”，越好。

### 2.5 聚合方式

#### Vulnerability 聚合

```text
sector_score = mean(该部门 6 个指标分数)
vulnerability = mean(6 个 sector_score)
```

六个部门等权；部门内六个指标也等权。

#### Readiness 聚合

```text
component_score = mean(该组成部分内指标分数)
readiness = mean(Economic, Governance, Social 三个 component_score)
```

三个 readiness 组成部分等权。Economic Readiness 只有一个主指标 Doing Business；Governance 有四个指标；Social 有四个指标，其中 ICT Infrastructure 本身又由四个 ICT 子变量合成。

#### ND-GAIN 总分

```text
ND-GAIN score = (Readiness score - Vulnerability score + 1) × 50
```

这一步将综合分数转换到 0–100 区间。

---

## 3. Vulnerability 的三个组成维度

### 3.1 Exposure 暴露度

官方定义：Exposure 是人类社会及其支撑部门受到未来气候条件变化压力的程度。它捕捉的是系统外部的物理因素。

官方网页进一步说明：Exposure 是从生物物理角度衡量系统对显著气候变化的暴露程度，独立于社会经济背景；Exposure 指标是未来几十年的 projected impacts，因此在 ND-GAIN 中 **随时间不变**。

**解读：**

- Exposure 更接近“未来气候冲击或物理气候风险会有多强”。
- 它通常来自气候模型、作物模型、水文模型、疾病传播模型、海平面或极端天气预测。
- Exposure 是 vulnerability 的一部分，所以其缩放后分数越高，表示越暴露、越脆弱。

### 3.2 Sensitivity 敏感性

官方定义：Sensitivity 是人群及其依赖部门受到气候扰动影响的程度。增加 sensitivity 的因素包括：

- 对气候敏感部门的依赖程度；
- 因地形、人口结构等因素而对气候危害特别敏感的人口比例。

官方网页说明：Sensitivity 可以随时间变化。

**解读：**

- Sensitivity 不是气候冲击本身，而是国家内部结构导致“同样冲击下更容易受伤”的程度。
- 例如食物进口依赖、农村人口、贫民窟人口、低海拔人口、进口能源依赖等。
- Sensitivity 是 vulnerability 的一部分，所以分数越高，表示越敏感、越脆弱。

### 3.3 Adaptive Capacity 适应能力

官方定义：Adaptive Capacity 是社会及其支撑部门调整以减少潜在损害、应对气候事件负面后果的能力。ND-GAIN 的 adaptive capacity 指标试图捕捉部门层面可用于应对气候影响的手段。

官方网页说明：Adaptive Capacity 表示部门特定适应所需社会资源的可得性，也会随时间变化。

**重要解读：**

概念上，adaptive capacity 越强越好；但它在 ND-GAIN vulnerability 框架中会被转换成 vulnerability score。因此：

- 原始能力越强，通常会转成更低的 vulnerability contribution；
- 标准化后的 adaptive capacity 分数越高，表示适应能力缺口越大，越脆弱。

---

## 4. Vulnerability 子指标：解读、构建方式与数据来源

下表按官方六个部门整理 36 个 vulnerability 指标。

### 4.1 Food 食物部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of cereal yields | 气候变化对主要粮食供给的预期影响。 | 比较 1980–2009 基准期与 2040–2069 未来期，在 RCP 4.5 下稻米、小麦、玉米产量变化。使用五个作物模型：EPIC、GEPIC、LPJmL、pDSSAT、PEGASUS。数据源：Earth System Grid Federation。 |
| Exposure | Projected population change | 未来人口增长带来的食物需求压力。 | 计算 2010 人口与 2020–2050 平均预测人口之间的百分比变化。数据源：World Bank HNPStats population projection。 |
| Sensitivity | Food import dependency | 食物进口依赖越高，越容易受国际价格和供应冲击影响。 | 食物进口占商品进口比例，包括食物、活体动物、饮料、烟草、动植物油脂等。数据源：World Bank, Food imports (% of merchandise imports)。 |
| Sensitivity | Rural population | 农村人口比例越高，通常意味着对气候敏感型农业或近自给农业依赖更强。 | 农村人口占总人口比例。数据源：WDI, Rural population (% of total population)。 |
| Adaptive Capacity | Agriculture capacity | 农业技术投入能力，反映农业系统可用于适应气候冲击的资源。 | 由四项农业技术指标构成：灌溉装备面积、化肥使用、农药使用、拖拉机使用。ND-GAIN 取四项中两个“最不脆弱”的分数平均。数据源：FAOSTAT 与 WDI。 |
| Adaptive Capacity | Child malnutrition | 儿童营养不良反映提供基本营养需求的能力不足。 | 5 岁以下儿童 wasting 比例；OECD 国家默认儿童营养不良率为 0。数据源：WDI, Prevalence of wasting (% of children under 5)。 |

### 4.2 Water 水部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of annual runoff | 气候变化对地表水资源的影响。 | 比较 1980–2009 与 2040–2069，在 RCP 4.5 下年径流变化；使用 CMIP5 中 6 个 GCM。数据源：WRI Aqueduct projected water risks。 |
| Exposure | Projected change of annual groundwater recharge | 气候变化对地下水补给的影响。 | 比较 1971–2000 与 2040–2069，在 RCP 4.5 下年地下水补给减少幅度；使用 5 个 GCM。数据源：Portmann et al. (2013) / Goethe University Frankfurt。 |
| Sensitivity | Freshwater withdrawal rate | 淡水取水压力越高，面对水资源减少时越敏感。 | 年淡水取水量占内部可再生水资源比例。数据源：AQUASTAT。 |
| Sensitivity | Water dependency ratio | 外部水资源依赖越高，越容易受跨境水资源冲突或供应变化影响。 | 可再生水资源中来自境外或受条约保障部分的比例。数据源：AQUASTAT。 |
| Adaptive Capacity | Dam capacity | 水坝库容代表调节淡水资源时空分布变化的能力。 | 人均水坝理论初始库容。数据源：AQUASTAT。 |
| Adaptive Capacity | Access to reliable drinking water | 安全可靠饮水服务覆盖率越高，说明供水管理与基础设施适应能力越强。 | 使用安全管理饮用水服务的人口比例。数据源：JMP, People using safely managed drinking water services (% of population)。 |

### 4.3 Health 健康部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of deaths from climate-change-induced diseases | 气候变化导致疾病负担增加的预期影响。 | 使用 DALY 模型估计 2000 基准到 2030 情景下气候相关疾病负担变化；不包括疟疾 DALY，因为媒介传播疾病另有指标。数据源：Ebi (2008)。 |
| Exposure | Projected change in vector-borne disease | 媒介传播疾病风险随气候变化的变化，主要以疟疾传播季长度表示。 | 使用 malaria LTS 预测，取四个疟疾模型与五个 GCM 的 ensemble mean，比较 1980–2010 与 2050，在 RCP 4.5 下的变化。数据源：Caminade et al. (2014)。 |
| Sensitivity | Dependency on external resources for health services | 卫生系统外部资金依赖越高，表示本国卫生服务内部能力较弱，对冲击更敏感。 | 外部来源卫生支出占当前卫生支出比例。数据源：WHO, External health expenditure (% of current health expenditure)。 |
| Sensitivity | Slum population | 贫民窟人口比例高意味着饮水、卫生、住房和人口密度条件差，面对气候冲击更敏感。 | 城市人口中生活在贫民窟住户的比例。数据源：UN-HABITAT。 |
| Adaptive Capacity | Medical staffs | 医生、护士、助产士数量代表基础医疗应对能力。 | 每千人 physicians、nurses and midwives 数量之和。数据源：WDI。 |
| Adaptive Capacity | Access to improved sanitation facilities | 安全卫生设施覆盖率越高，越能减少传染病和灾害后的健康风险。 | 使用安全管理卫生服务的人口比例。数据源：JMP, People using safely managed sanitation services (% of population)。 |

### 4.4 Ecosystem Services 生态系统服务部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of biome distribution | 气候变化导致陆地生物群系分布改变，威胁生态系统功能。 | 使用动态植被模型 MC1，计算 2070–2100 相对 1990 年国家陆地面积中可能转变为其他潜在生物群系的比例。数据源：Gonzalez et al. (2010)。 |
| Exposure | Projected change of marine biodiversity | 气候变化对海洋生物多样性和渔业资源的影响。 | 基于 1066 种商业鱼类和无脊椎动物的气候包络模型，计算 2050 相对 2001–2005 的物种 turnover，并按各国 EEZ 聚合；内陆国设为 0。数据源：Cheung et al. (2009)。 |
| Sensitivity | Natural capital dependency | 对生态系统服务依赖越高，越容易受生态系统气候冲击影响。 | 自然资本占总财富比例；自然资本包括作物、牧场、森林、保护区等，不包括石油、天然气、矿产。数据源：World Bank, Changing Wealth of Nations。 |
| Sensitivity | Ecological footprint | 生态需求相对于生态承载能力的压力。生态赤字越高，适应选择越少。 | 比较生活方式对生态服务需求与国家生态承载/再生能力之间的盈余或赤字。数据源：National Footprint and Biocapacity Accounts。 |
| Adaptive Capacity | Protected biomes | 生物群系保护程度代表持续保护和管理生态系统服务的能力。 | 使用 Yale EPI 的 Terrestrial Protected Areas 指标，按各生物群系占国土比例加权，衡量达到 17% 保护目标的程度。数据源：Environmental Performance Index。 |
| Adaptive Capacity | Engagement in international environmental conventions | 参与国际环境公约反映参与多边谈判、达成国内行动共识的能力。 | 根据签署、批准、退出等状态构造一国环境条约参与程度相对最大值的比例。数据源：Environmental Treaties and Resource Indicators。 |

### 4.5 Human Habitat 人居部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of warm periods | 极端高温或暖期持续时间增加对人居条件构成威胁。 | 使用 Warm Spell Duration Index (WSDI)，比较 1960–1990 与 2040–2070，在 RCP 4.5 下的绝对变化。数据源：Sillmann et al. CMIP5 climate extremes indices。 |
| Exposure | Projected change of flood hazard | 极端连续降水增加带来的洪水风险。 | 使用 rx5day，即月最大连续 5 日降水量；比较 1960–1990 与 2040–2070，在 RCP 4.5 下的变化；由 19 个 GCM 的 extreme indices 生成。数据源：Sillmann et al.。 |
| Sensitivity | Urban concentration | 城市人口高度集中时，气候冲击可能影响更多人口和资产。 | Herfindahl 城市人口集中度 × 城市化率；没有 75 万以上大城市的国家设为 0。数据源：UN Population Division, World Urbanization Prospects。 |
| Sensitivity | Age dependency ratio | 儿童和老年人口比例越高，对气候冲击越敏感。 | 0–14 岁人口比例加 65 岁及以上人口比例。数据源：WDI。 |
| Adaptive Capacity | Quality of trade and transport infrastructure | 贸易与交通基础设施质量越高，迁移、救援、供应和恢复能力越强。 | 物流专业人士对港口、铁路、道路、IT 等基础设施质量的 1–5 评分。数据源：WDI / Logistics Performance 相关指标。 |
| Adaptive Capacity | Paved roads | 铺装道路比例代表道路系统稳固性，特别是农村交通改善能力。 | 铺装道路长度占全国道路总长度比例。数据源：International Roads Federation。 |

### 4.6 Infrastructure 基础设施部门

| 维度 | 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|---|
| Exposure | Projected change of hydropower generation capacity | 气候变化通过水文变化影响水电发电能力。 | 计算 2005 到 2050 水电发电能力变化，并按一国水电依赖程度加权。数据源：Hamududu & Killingtveit (2012) 与水电依赖数据。 |
| Exposure | Projected change of sea-level-rise impacts | 海平面上升和风暴潮对沿海基础设施的潜在影响。 | 使用全球地形/海底地貌数据，估算邻海且低于约 4 米的陆地面积比例；4 米来自 RCP 4.5 下高端海平面上升 0.63 米加中等风暴潮约 3 米；内陆国设为无沿海风险。 |
| Sensitivity | Dependency on imported energy | 进口能源依赖高意味着更容易受价格波动和供应中断影响。 | 能源使用中进口能源比例。数据源：IEA World Energy Balances。 |
| Sensitivity | Population living under 5m above sea level | 低海拔人口越多，越容易受海平面上升、风暴潮等沿海风险影响。 | 居住在海拔 5 米或以下地区的人口占总人口比例。数据源：WDI。 |
| Adaptive Capacity | Electricity access | 电力可及性支持医疗、灾害救援、食品储存、教育和 ICT，是基础设施适应能力的重要条件。 | 接入电网供电的人口比例。数据源：WDI, Access to electricity (% of population)。 |
| Adaptive Capacity | Disaster preparedness | 国家灾害风险降低战略的采用和实施程度，反映自然灾害应对能力。 | 使用 UN SDG 13.1.2，衡量国家是否采用并实施符合 Sendai Framework 2015–2030 的国家减灾战略。数据源：UN Sustainable Development Goals Indicators database。 |

---

## 5. Readiness 子指标：解读、构建方式与数据来源

### 5.1 Economic Readiness 经济准备度

| 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|
| Ease of Doing Business index | 衡量一国商业环境是否有利于吸引和使用适应投资。 | 使用 World Bank Doing Business 指标。DB 原始框架包括 10 个主题、40 个指标。ND-GAIN 使用 DB 原始数据并按 DB 方法构建 2003–2020 年的得分；各主题按百分位排名，10 个主题平均形成最终 DB 分数。数据源：World Bank Doing Business。 |

Doing Business 的 10 个主题包括：

1. Starting a Business 开办企业
2. Dealing with Construction Permits 办理施工许可
3. Getting Electricity 获得电力
4. Registering Property 登记财产
5. Getting Credit 获得信贷
6. Protecting Investors 保护投资者
7. Paying Taxes 纳税
8. Trading Across Borders 跨境贸易
9. Enforcing Contracts 执行合同
10. Resolving Insolvency 破产处理

### 5.2 Governance Readiness 治理准备度

| 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|
| Political stability and non-violence | 政治稳定和无暴力环境有助于降低投资风险，吸引适应投资。 | 直接取 World Governance Indicators (WGI) 的 Political Stability and Absence of Violence/Terrorism: Estimate。 |
| Control of corruption | 腐败控制反映政府完整性、问责能力和资金使用可信度。 | 直接取 WGI Control of Corruption: Estimate，基于企业、家庭、公共/私人/NGO 专家对公共权力谋私和国家俘获的感知。 |
| Regulatory quality | 高质量监管有助于制定和实施促进私营部门发展及适应行动的政策。 | 直接取 WGI Regulatory Quality: Estimate，衡量政府制定和执行促进私营部门发展的政策与监管的能力。 |
| Rule of law | 法治质量影响合同执行、产权保护、法院、警察、犯罪和暴力风险，从而影响投资环境。 | 直接取 WGI Rule of Law: Estimate。 |

### 5.3 Social Readiness 社会准备度

| 指标 | 解读 | 构建方式 / 数据 |
|---|---|---|
| Social inequality | 社会不平等越低，社会越可能公平且有效地使用适应投资。 | 使用最贫困 20% 人口在国民收入或消费中的份额。份额越高，通常意味着分配更平等。数据源：MDG Indicators。 |
| ICT infrastructure | ICT 基础设施提高信息传播、市场连接和适应行动实施能力。 | 由四个 ICT 子指标平均构成：每百人移动电话订阅、每百人固定电话订阅、每百人固定宽带订阅、互联网使用者比例。数据源：WDI 与 ITU。 |
| Education | 教育水平提高社会吸收、设计和实施适应方案的能力。 | 高等教育毛入学率，即 tertiary gross enrollment ratio。数据源：WDI。 |
| Innovation | 创新能力帮助形成适应气候变化所需的研究、技术和解决方案。 | 居民专利申请数除以人口，构造人均居民专利申请。数据源：WDI Patent applications, residents 与 Population。 |

---

## 6. 使用这些字段时的经验性解读

### 6.1 如果研究绝对水平

使用：

```text
vulnerability
readiness
```

解释为：

- 一个国家绝对意义上有多脆弱；
- 一个国家绝对意义上有多准备好利用投资开展适应行动。

### 6.2 如果研究相对于经济发展水平的表现

使用：

```text
vulnerability_delta
readiness_delta
```

解释为：

- 在相同 GDP per capita 预期下，该国表现是否更好或更差；
- 适合做“超出经济发展水平解释之外的制度、政策、结构表现”分析。

### 6.3 如果研究气候物理风险暴露

优先看：

```text
exposure
```

注意：ND-GAIN 官方网页说明，Exposure 是 projected impacts for coming decades，因此在 ND-GAIN 中随时间不变。

### 6.4 如果研究社会经济易损性

优先看：

```text
sensitivity
```

Sensitivity 可以随时间变化，适合描述一国社会经济结构、人口结构和部门依赖导致的易损性。

### 6.5 如果研究适应能力缺口

可看：

```text
adaptive_capacity
```

但要注意方向：在 vulnerability 分数体系下，adaptive capacity 的标准化分数越高通常表示适应能力缺口越大、对 vulnerability 的贡献越高。

---

## 7. 主要官方来源

1. University of Notre Dame Global Adaptation Initiative. **Country Index Technical Report**. Updated August 26, 2024. 用户上传文件：`nd_gain_countryindex_technicalreport_2024(3).pdf`。
2. ND-GAIN Index 官方 Methodology 页面：`https://gain-new.crc.nd.edu/about/methodology`。
3. ND-GAIN 官方 Download Data 页面：`https://gain.nd.edu/our-work/country-index/download-data/` 与 `https://gain-new.crc.nd.edu/about/download`。

