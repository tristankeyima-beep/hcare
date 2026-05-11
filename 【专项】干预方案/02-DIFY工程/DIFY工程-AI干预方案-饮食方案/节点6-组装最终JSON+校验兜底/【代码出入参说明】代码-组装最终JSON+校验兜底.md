# 代码节点出入参说明：组装最终JSON+校验兜底

对应代码：`代码-组装最终JSON+校验兜底.py`

## 这个节点做什么

把 LLM 生成的顶层总述字段、普通建议 `groups/items`、7 天菜谱 `meal_plan_group` 组装成最终标准 JSON，并做结构校验和兜底。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `plan_header` | String(JSON) | 否 | 节点5-2输出的打包字段，包含 `plan_name`、`plan_title`、`plan_summary`、`execution_points`。DIFY 中建议传 `{{#节点5-2.plan_header#}}`。 |
| `plan_name` | String | 否 | 兼容散字段传入；仅当 `plan_header` 为空或无法解析时使用。 |
| `plan_title` | String | 否 | 兼容散字段传入；仅当 `plan_header` 为空或无法解析时使用。 |
| `plan_summary` | String | 否 | 兼容散字段传入；仅当 `plan_header` 为空或无法解析时使用。 |
| `execution_points` | String | 否 | 兼容散字段传入；仅当 `plan_header` 为空或无法解析时使用。 |
| `group_plan` | Object/Array 或 JSON字符串 | 否 | 可选。若后续恢复独立分组规划节点，可用于按规划顺序排序 groups。当前 6 节点版本通常不传。 |
| `groups` | Object/Array 或 JSON字符串 | 否 | 节点3-2输出，包含普通饮食建议分组。 |
| `meal_plan_group` | Object 或 JSON字符串 | 否 | 节点4-2输出，包含 `group_type=weekly_meal_plan` 的 7 天菜谱分组。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `final_plan_json_text` | String(JSON) | H5 可解析渲染的最终饮食方案 JSON 字符串。Dify Code 节点不直接返回深层 Object，避免超过对象深度限制。 |
| `validation_errors` | String(JSON Array) | 结构校验错误数组的 JSON 字符串。为空数组字符串表示结构满足当前渲染要求。 |
| `validation_errors_count` | Number | 结构校验错误数量。 |
| `groups_count` | Number | 最终输出中的 group 数量。 |

## 校验规则

- 顶层必须包含非空 `plan_name`、`plan_title`、`plan_summary`、`execution_points`。
- `groups` 必须是非空数组。
- 每个 group 必须包含 `group_title` 和非空 `items`。
- 每个 item 必须包含 `content`、`focus_point`、`importance`。
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`；非法值会被归一为 `常规建议`。
- 普通建议 group 默认补 `group_type=advice_list`。
- 菜谱 group 固定补 `group_type=weekly_meal_plan`，并追加到 `groups` 末尾。
- `weekly_meal_plan` 必须包含 7 个 `daily_meal_plan` item。
- 每天必须包含早餐、午餐、晚餐。
- 每个食物必须包含 `name`、`amount_g`、`kcal`、`protein_g`、`fat_g`。

## 兜底策略

- 最终方案只以 `final_plan_json_text` 字符串输出，不以 Object 输出，也不重复输出 `final_plan_json`，避免 Dify Code 节点报 `Depth limit 5 reached, object too deep` 或误配变量类型。
- 顶层文案优先从 `plan_header` 解析；如果没有传 `plan_header`，则把 `plan_name`、`plan_title`、`plan_summary`、`execution_points` 四个散字段临时组装成顶层文案对象。
- 顶层字段缺失时使用默认饮食方案文案。
- 某个 item 缺少 `focus_point` 时补默认提醒。
- 没有可用 group 时输出一个最小可渲染的“饮食总原则”分组。
- 如传入 `group_plan`，按其中的 `group_title` 顺序排序最终 groups；当前版本通常按节点3-2输出顺序保留。
- 保留 item 上的菜谱扩展字段，避免把 `meals`、热量、蛋白质、脂肪等执行字段过滤掉。
