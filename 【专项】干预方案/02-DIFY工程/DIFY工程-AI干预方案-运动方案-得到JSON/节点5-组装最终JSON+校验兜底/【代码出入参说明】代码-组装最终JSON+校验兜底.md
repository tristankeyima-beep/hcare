# 代码节点出入参说明：组装最终JSON+校验兜底

对应代码：`代码-组装最终JSON+校验兜底.py`

## 这个节点做什么

把节点3和节点4保护后的出参组装成最终标准 JSON，并做结构校验和兜底。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `planHeader` | Object 或 JSON字符串 | 否 | 节点4保护代码输出，包含 `planName`、`planTitle`、`planSummary`、`executionPoints`。 |
| `groupPlan` | Object/Array 或 JSON字符串 | 否 | 节点3保护代码输出，用于按规划顺序排序 groups。 |
| `groups` | Object/Array 或 JSON字符串 | 否 | 节点3保护代码输出，包含最终方案条目。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `finalPlanJson` | Object | H5 可直接渲染的最终运动方案 JSON。 |
| `finalPlanJsonText` | String | `finalPlanJson` 的 JSON 字符串版本。 |
| `validationErrors` | Array<String> | 结构校验错误。为空表示结构满足当前渲染要求。 |
| `validationErrorsCount` | Number | 结构校验错误数量。 |
| `groupsCount` | Number | 最终输出分组数量。 |

## 校验规则

- 顶层必须包含非空 `planName`、`planTitle`、`planSummary`、`executionPoints`。
- `groups` 必须是非空数组。
- 每个 group 必须包含 `groupTitle` 和非空 `items`。
- 每个 item 必须包含 `content`、`focusPoint`、`importance`。
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`；非法值会被归一为 `常规建议`。

## 兜底策略

- 顶层字段缺失时使用默认运动方案文案。
- 某个 item 缺少 `focusPoint` 时补默认提醒。
- 没有可用 group 时输出一个最小可渲染的“运动总原则”分组。
- 按 `groupPlan` 中的 `groupTitle` 顺序排序最终 groups。
