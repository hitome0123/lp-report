# Phase 2 — LLM分析与结构化

## 目标
用 GPT-4o 将搜索结果结构化为 JSON，生成同行对比矩阵和投资逻辑评估。

## 输入
- `company_data_raw` — Phase 1 Agent 2 的搜索结果（原始文本）
- `industry_data_raw` — Phase 1 Agent 3 的搜索结果（原始文本）

## 3个分析任务

### 任务1: 公司数据结构化
- 提取融资轮次、估值、营收、客户、技术规格
- 输出 `company_data.json`（28个字段）
- Prompt: "将以下搜索结果结构化为JSON，严格按schema输出"

### 任务2: 同行对比矩阵
- 4家公司 × 7个维度（市值/营收/增速/P.S/核心产品/退出状态）
- 计算 Cerebras P/S 倍数（估值/营收）
- 输出 `comparison_matrix.json`

### 任务3: 投资逻辑兑现评估
- 读取用户 `user_response.json` 的3个thesis
- 评估每个thesis的兑现度（超预期/符合预期/低于预期/已修复）
- 输出 `thesis_assessment.json`

## Token预算
| 任务 | Input | Output | Cost |
|------|-------|--------|------|
| 公司结构化 | ~8K | ~2K | $0.048 |
| 同行对比 | ~6K | ~1.5K | $0.032 |
| 逻辑评估 | ~10K | ~3K | $0.067 |

## 达标判断
- company_data.json 有 ≥20个字段 → ✅
- 同行数据覆盖 ≥3家 → ✅
- 3个thesis都有评估 → ✅
