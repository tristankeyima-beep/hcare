# 代码节点：保护素材摘要 LLM 出参

## 输入

- `llmText` 或 `text`：节点2 LLM 输出文本。

## 输出

- `materialSummaryBundle`：JSON 字符串。
- `medicalStatusSummary`
- `reviewNeedSummary`
- `safetyTriggerSummary`

## 规则

- 兼容 LLM 输出前后夹带解释文字的情况。
- 缺失字段用“暂无可提炼...”兜底。
