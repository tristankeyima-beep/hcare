# 代码节点：保护顶层总述 LLM 出参

## 输入

- `llmText` 或 `text`：节点4 LLM 输出文本。

## 输出

- `planHeader`：JSON 字符串。
- `planName`
- `planTitle`
- `planSummary`
- `executionPoints`

## 规则

- 兼容 LLM 输出前后夹带解释文字的情况。
- 缺失字段使用健康周报默认文案兜底。
