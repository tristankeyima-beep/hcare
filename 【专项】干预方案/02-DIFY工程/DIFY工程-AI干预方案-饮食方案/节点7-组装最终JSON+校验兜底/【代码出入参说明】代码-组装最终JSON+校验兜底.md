# 代码节点出入参说明：组装最终JSON+校验兜底

对应代码：`代码-组装最终JSON+校验兜底.py`

## 这个节点做什么

把 LLM 生成的顶层总述字段、分组规划和 `groups/items` 组装成最终标准 JSON，并做结构校验和兜底。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `plan_header` | Object 或 JSON字符串 | 否 | 节点6输出，包含 `plan_name`、`plan_title`、`plan_summary`、`execution_points`。 |
| `group_plan` | Object/Array 或 JSON字符串 | 否 | 节点4输出，用于按规划顺序排序 groups。 |
| `groups` | Object/Array 或 JSON字符串 | 否 | 节点5输出，包含最终方案条目。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `final_plan_json` | Object | H5 可直接渲染的最终饮食方案 JSON。 |
| `final_plan_json_text` | String | `final_plan_json` 的 JSON 字符串版本。 |
| `validation_errors` | Array<String> | 结构校验错误。为空表示结构满足当前渲染要求。 |

## 校验规则

- 顶层必须包含非空 `plan_name`、`plan_title`、`plan_summary`、`execution_points`。
- `groups` 必须是非空数组。
- 每个 group 必须包含 `group_title` 和非空 `items`。
- 每个 item 必须包含 `content`、`focus_point`、`importance`。
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`；非法值会被归一为 `常规建议`。

## 兜底策略

- 顶层字段缺失时使用默认饮食方案文案。
- 某个 item 缺少 `focus_point` 时补默认提醒。
- 没有可用 group 时输出一个最小可渲染的“饮食总原则”分组。
- 按 `group_plan` 中的 `group_title` 顺序排序最终 groups。

