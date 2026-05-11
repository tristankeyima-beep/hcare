# 代码节点出入参说明：格式化7天菜谱group

对应代码：`代码-格式化7天菜谱group.py`

## 这个节点做什么

放在两个菜谱 LLM 节点之后，把“第1-3天”和“第4-7天”的 `meal_plan_group` 解析、合并、归一和兜底为后续节点可稳定引用的 JSON 字符串。

该节点只做结构格式化和轻量校验提醒，不重新生成菜谱内容。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `meal_plan_group_1_3` | Object 或 JSON字符串 | 否 | 节点4-1A输出，第1-3天菜谱。可以是完整 `meal_plan_group` 对象，也可以是包含 `meal_plan_group` 的对象。 |
| `meal_plan_group_4_7` | Object 或 JSON字符串 | 否 | 节点4-1B输出，第4-7天菜谱。可以是完整 `meal_plan_group` 对象，也可以是包含 `meal_plan_group` 的对象。 |
| `text_1_3` | String | 否 | 未开启结构化输出时，传入节点4-1A的整段 JSON 文本。 |
| `text_4_7` | String | 否 | 未开启结构化输出时，传入节点4-1B的整段 JSON 文本。 |
| `meal_plan_group` | Object 或 JSON字符串 | 否 | 兼容旧版单节点 7 天菜谱输入；分段模式下通常不传。 |
| `text` | String | 否 | 兼容旧版单节点 7 天菜谱文本；分段模式下通常不传。 |
| `llm_text` | String | 否 | 兼容字段，作用同 `text`。 |
| `llm_output` | Object/String | 否 | 兼容字段，可传 LLM 原始输出对象。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `meal_plan_group` | String(JSON) | 格式化后的菜谱 group，供节点6引用。 |
| `formatted_meal_plan_group_json` | String(JSON) | 包含顶层 `meal_plan_group` 的完整 JSON 字符串，便于调试或透传。 |
| `meal_plan_days_count` | Number | 当前有效菜谱天数。 |
| `format_warnings` | String(JSON Array) | 格式化过程中的结构提醒。为空数组字符串表示未发现结构问题。 |

## 归一规则

- 固定 `group_type=weekly_meal_plan`。
- 固定 `display_style=weekly_meal_plan`。
- 移除内部枚举字段 `diet_plan_goal`，保留 `diet_plan_goal_label` 和 `goal_basis`。
- 合并第1-3天与第4-7天，按 `day` 升序排序。
- 如果同一天重复，保留首次出现的菜谱，并在 `format_warnings` 提醒。
- 每天 item 固定 `item_type=daily_meal_plan`。
- `meal_name` 会归一餐次名称：如 `午餐（食堂可选）` 会转为 `meal_name=午餐`、`meal_scene=食堂可选`。
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`，非法值归一为 `重点执行`。
- 数值字段会尽量转为数字；无法转换时兜底为 `0`。
- 每餐食物必须有 `name` 才会保留。

## 校验提醒

该节点会把以下问题写入 `format_warnings`：

- 菜谱不是 7 天。
- 合并后缺少某些天数或出现重复天数。
- 某天缺少早餐、午餐或晚餐。
- 某餐缺少有效 `foods`。
- 某个食物缺少 `name`。
- LLM 输出无法解析为 `meal_plan_group` 对象。

最终严格校验仍由节点6统一完成。
