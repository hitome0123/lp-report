# Phase 1 — 并行DDG搜索

## 目标
用DDG搜索引擎采集目标公司和行业的公开数据，输出两个结构化JSON。

## 执行方式
Dispatch 2个并行subagent（Agent 2 + Agent 3），各自独立搜索，互不依赖。

---

## Agent 2: 目标公司搜索

### 搜索词（以Cerebras为例，替换{company}即可复用）

```python
queries = [
    '"{company}" funding rounds series valuation investors',
    '"{company}" IPO filing SEC S-1 2024 2025 2026 Nasdaq',
    '"{company}" revenue customers contracts partnerships',
    '"{company}" founders team CEO CTO background',
    '"{company}" product technology chip specifications',
    '"{company}" Wafer Scale Engine WSE-3 performance benchmark',
    '"{company}" CFIUS review G42 regulatory',
    '"{company}" latest news 2026',
    'Crunchbase "{company}" total funding',
]
```

### 搜索方法

```python
from duckduckgo_search import DDGS

def search_ddg(query, max_results=10):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return results  # [{title, href, body}, ...]
```

如果 `duckduckgo-search` 未安装或DDG封禁，降级到 Claude 内置 WebSearch 工具。

### 输出Schema: company_data.json

```json
{
  "company_name": "Cerebras Systems",
  "founded": "2016",
  "hq": "Sunnyvale, CA",
  "founders": ["Andrew Feldman (CEO)", "..."],
  "core_product": "Wafer-Scale Engine (WSE-3)",
  "tech_specs": {
    "transistors": "4 trillion",
    "die_size": "46,225 mm²",
    "ai_cores": 900000,
    "peak_flops": "125 PFLOPS (FP16)",
    "memory": "44 GB on-chip SRAM",
    "process_node": "TSMC 5nm"
  },
  "funding_rounds": [
    {"round": "Series A", "date": "2016-05", "amount_m": 27, "valuation_b": null, "lead_investors": ["Benchmark"]},
    {"round": "Series B", "date": "2016-12", "amount_m": 25, "valuation_b": null, "lead_investors": ["Coatue"]},
    "..."
  ],
  "total_funding_b": 2.82,
  "latest_valuation_b": 23.0,
  "revenue_estimate_m": 500,
  "revenue_growth_pct": 535,
  "key_customers": ["OpenAI ($10B)", "Meta", "Mistral AI", "US DoD", "..."],
  "ipo_status": {
    "expected": "Q2 2026",
    "exchange": "Nasdaq",
    "ticker": "CBRS",
    "timeline": ["2024-08 秘密S-1", "2024-09 公开S-1", "2025-03 CFIUS通过", "2025-10 撤回", "2025底 重新提交"]
  },
  "risks": ["NVIDIA生态竞争", "大客户集中度", "TSMC产能依赖"],
  "sources": ["Crunchbase", "TechCrunch", "Bloomberg", "SEC EDGAR"]
}
```

### 达标判断
- 融资轮次 ≥5轮 → ✅
- 有明确估值数据 ≥2个时间点 → ✅
- 有营收/客户数据 → ✅
- 有IPO状态信息 → ✅
- 以上任一缺失 → 补充搜索词重跑

---

## Agent 3: 行业+同行搜索

### 搜索词

```python
queries = [
    'AI chip market size 2023 2024 2025 2028 2030 billion CAGR',
    'Gartner IDC AI semiconductor revenue forecast',
    'NVIDIA revenue 2025 2026 fiscal year annual report',
    'AMD revenue 2025 market share AI chip Instinct',
    'Intel Habana Gaudi revenue AI accelerator',
    'Graphcore SoftBank acquisition 2024 valuation',
    'semiconductor VC funding 2023 2024 2025 record',
    'CB Insights semiconductor funding quarterly',
    'CHIPS Act recipients funding awards 2024',
    'EY Ernst Young US IPO report 2025 technology semiconductor',
    'Arm Holdings IPO valuation performance 2023',
    'semiconductor IPO 2024 2025 Astera Labs',
]
```

### 输出Schema: industry_data.json

```json
{
  "market_size": {
    "source": "Market.us (narrow scope, AI accelerator only)",
    "data": [
      {"year": 2020, "size_b": 8.0, "growth_pct": null},
      {"year": 2021, "size_b": 11.2, "growth_pct": 40},
      "..."
    ],
    "cagr": "31%",
    "period": "2023-2028"
  },
  "competitors": [
    {
      "name": "NVIDIA",
      "market_cap": "$4.07T",
      "revenue_b": 215.9,
      "revenue_growth_pct": 65,
      "rd_pct": 8.6,
      "ps_ratio": 19,
      "market_share_pct": 86,
      "core_product": "H100 / B200 (Blackwell)",
      "employees": 36000
    },
    "..."
  ],
  "vc_trends": {
    "data": [
      {"year": 2018, "amount_b": 2.0, "deal_count": 150},
      "..."
    ],
    "subsectors": {
      "ai_chip_pct": 42,
      "power_semi_pct": 11,
      "optical_pct": 9,
      "other_pct": 38
    }
  },
  "chips_act": {
    "total_b": 52.7,
    "awarded_b": 33.7,
    "top_recipients": [
      {"company": "Intel", "amount_b": 7.86},
      {"company": "TSMC", "amount_b": 6.6},
      "..."
    ]
  },
  "notable_ipos": [
    {"company": "Arm Holdings", "date": "2023-09", "valuation": "$54.5B", "exchange": "Nasdaq"},
    "..."
  ],
  "ey_ipo_findings": {
    "us_ipo_count_2025": 216,
    "us_ipo_proceeds_2025_b": 47.4,
    "key_trend": "AI and defense-related tech expected to lead 2026 pipeline"
  },
  "sources": ["Gartner", "Market.us", "Crunchbase", "EY", "CB Insights", "SIA"]
}
```

### 达标判断
- 市场规模有 ≥5 年数据 → ✅
- 同行数据覆盖 ≥3 家(NVIDIA/AMD + 1) → ✅
- VC趋势有 ≥5 年数据 → ✅
- 有安永IPO相关数据 → ✅
