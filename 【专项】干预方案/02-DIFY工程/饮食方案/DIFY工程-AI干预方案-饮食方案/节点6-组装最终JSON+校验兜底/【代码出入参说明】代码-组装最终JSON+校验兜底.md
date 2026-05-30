# 代码节点出入参说明：组装最终JSON+校验兜底

对应代码：`代码-组装最终JSON+校验兜底.py`

## 这个节点做什么

把 LLM 生成的顶层总述字段、普通建议 `groups/items`、7 天菜谱 `mealPlanGroup` 组装成最终标准 JSON，并做结构校验和兜底。

当前 Dify yml 实际绑定方式：

- `planHeader: String(JSON) <= 将LLM生成的总述结构化.planHeader`
- `groups: String(JSON Array) <= 将饮食建议清单结构化.groups`
- `mealPlanGroup: String(JSON) <= 将七天菜谱结构化.mealPlanGroup`
- `planName`、`planTitle`、`planSummary`、`executionPoints` 同时接入字符串散字段，作为 `planHeader` 解析失败时的兜底。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `planHeader` | String(JSON) | 否 | 节点5-2输出的打包字段，包含 `planName`、`planTitle`、`planSummary`、`executionPoints`。DIFY 中建议传 `{{#节点5-2.planHeader#}}`。 |
| `planName` | String | 否 | 兼容散字段传入；仅当 `planHeader` 为空或无法解析时使用。 |
| `planTitle` | String | 否 | 兼容散字段传入；仅当 `planHeader` 为空或无法解析时使用。 |
| `planSummary` | String | 否 | 兼容散字段传入；仅当 `planHeader` 为空或无法解析时使用。 |
| `executionPoints` | String | 否 | 兼容散字段传入；仅当 `planHeader` 为空或无法解析时使用。 |
| `groupPlan` | String(JSON Array) | 否 | 可选。若后续恢复独立分组规划节点，可用于按规划顺序排序 groups。当前 yml 通常不传。 |
| `groups` | String(JSON Array) | 否 | 当前 yml 实际绑定字段，节点3-2输出，包含普通饮食建议分组。 |
| `mealPlanGroup` | String(JSON) | 否 | 当前 yml 实际绑定字段，节点4-2输出，包含 `groupType=weeklyMealPlan` 的 7 天菜谱分组。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `finalPlanJsonText` | String(JSON) | H5 可解析渲染的最终饮食方案 JSON 字符串。Dify Code 节点不直接返回深层 Object，避免超过对象深度限制。 |
| `validationErrors` | String(JSON Array) | 结构校验错误数组的 JSON 字符串。为空数组字符串表示结构满足当前渲染要求。 |
| `validationErrorsCount` | Number | 结构校验错误数量。 |
| `groupsCount` | Number | 最终输出中的 group 数量。 |

## 校验规则

- 顶层必须包含非空 `planName`、`planTitle`、`planSummary`、`executionPoints`。
- `groups` 必须是非空数组。
- 每个 group 必须包含 `groupTitle` 和非空 `items`。
- 每个 item 必须包含 `content`、`focusPoint`、`importance`。
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`；非法值会被归一为 `常规建议`。
- 普通建议 group 默认补 `groupType=adviceList`。
- 菜谱 group 固定补 `groupType=weeklyMealPlan`，并追加到 `groups` 末尾。
- `weeklyMealPlan` 必须包含 7 个 `dailyMealPlan` item。
- 每天必须包含早餐、午餐、晚餐。
- 每个食物必须包含 `name`、`amountG`、`kcal`、`proteinG`、`fatG`。
- 最终输出会按层级补齐字段：所有 group 使用同一组字段，所有 item 使用同一组字段；meal 和 food 层也会补齐同层级字段。

## 兜底策略

- 最终方案只以 `finalPlanJsonText` 字符串输出，不以 Object 输出，也不重复输出 `finalPlanJson`，避免 Dify Code 节点报 `Depth limit 5 reached, object too deep` 或误配变量类型。
- 顶层文案优先从 `planHeader` 解析；如果没有传 `planHeader`，则把 `planName`、`planTitle`、`planSummary`、`executionPoints` 四个散字段临时组装成顶层文案对象。
- 顶层字段缺失时使用默认饮食方案文案。
- 某个 item 缺少 `focusPoint` 时补默认提醒。
- 没有可用 group 时输出一个最小可渲染的“饮食总原则”分组。
- 如传入 `groupPlan`，按其中的 `groupTitle` 顺序排序最终 groups；当前版本通常按节点3-2输出顺序保留。
- 保留 item 上的菜谱扩展字段，避免把 `meals`、热量、蛋白质、脂肪等执行字段过滤掉。
- 当某类字段只存在于部分 type 时，例如 `weeklyMealPlan` 的 `dietPlanGoalLabel`、`goalBasis`，或 `dailyMealPlan` 的 `day`、`dailyTotalKcal`、`meals`，其他 group/item 会补同名字段；标量补空字符串，数组补空数组，对象补空对象。
