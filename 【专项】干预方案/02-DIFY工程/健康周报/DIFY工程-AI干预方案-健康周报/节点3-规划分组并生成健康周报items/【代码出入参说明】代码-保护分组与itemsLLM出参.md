# 代码节点：保护分组与 items LLM 出参

## 输入

- `llmText` 或 `text`：节点3 LLM 输出文本。

## 输出

- `groupPlan`：JSON 字符串，包含 `groupPlan` 数组。
- `groups`：JSON 字符串，包含 `groups` 数组。
- `groupsCount`

## 规则

- 兼容 LLM 输出前后夹带解释文字的情况。
- `groupType` 固定为 `adviceList`，`displayStyle` 固定为 `list`。
- 非法 `importance` 降级为 `常规建议`。
- 空内容 item 会被丢弃。
