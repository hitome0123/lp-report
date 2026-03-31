# 数据来源与置信度矩阵

## 每页数据来源

| 报告页 | 数据项 | 主要来源 | 备用来源 | 置信度 |
|--------|--------|---------|---------|--------|
| P1 封面 | 投资组合 | 客户回复 | — | 高 |
| P3 逻辑兑现 | 3个thesis | client_response.json | — | 高 |
| P3 逻辑兑现 | 兑现证据 | DDG搜索+SEC | Bloomberg | 高 |
| P4 同行对比 | NVIDIA营收 | NVIDIA 10-K | Yahoo Finance | 高 |
| P4 同行对比 | AMD营收 | AMD 10-K | Earnings报道 | 高 |
| P4 同行对比 | Cerebras营收 | SEC S-1 | Bloomberg | 高 |
| P4 市场规模 | AI加速器$49B | Bloomberg Intelligence | Silicon Analysts | 中 |
| P5 融资历程 | 8轮数据 | Crunchbase | SEC S-1 | 高 |
| P5 融资历程 | 估值轨迹 | Bloomberg | 官方PR | 高 |
| P5 技术参数 | WSE-3规格 | 官方技术文档 | ServeTheHome | 高 |
| P5 IPO时间线 | 6个节点 | SEC EDGAR | TechCrunch | 高 |
| P6 风险 | 风险评估 | 客户回复+LLM | — | 中 |
| P7 数据速览 | 13项汇总 | 各页数据汇总 | — | 高 |

## 搜索降级链

```
DuckDuckGo（首选，免费）
  ↓ 搜索失败/封禁
WebSearch（Claude内置）
  ↓ 不可用
Tavily MCP（如已配置）
```

## 数据口径说明

| 数据项 | 口径 | 注意 |
|--------|------|------|
| AI加速器市场规模 | 仅AI加速器芯片（GPU/TPU/ASIC），不含通用半导体 | 旧版误用$30B（含整体半导体），已修正为$15B→$49B |
| NVIDIA营收 | Fiscal Year（1月结束），FY2026=CY2025.02-2026.01 | 不是Calendar Year |
| Cerebras TTM营收 | H1 2024 $136.4M + H2增速推算 | 中等置信度，非官方确认 |
| P/S倍数 | 基于全年营收~$272M，非TTM $206.5M | 两种口径差异：~85x vs ~112x |
