# 代码节点：组装最终 JSON + 校验兜底

## 输入

- `planHeader`：节点4 输出的顶层字段 JSON 字符串。
- `groupPlan`：节点3 输出的分组规划 JSON 字符串。
- `groups`：节点3 输出的分组建议 JSON 字符串。

## 输出

- `finalPlanJson`
- `finalPlanJsonText`
- `validationErrors`
- `validationErrorsCount`
- `groupsCount`

## 规则

- 输出结构沿用通用 `groups/items`。
- 不新增 H5 专用时间轴字段。
- 非法 `importance` 降级为 `常规建议`。
- 无有效分组时输出“健康周报总原则”兜底组。
