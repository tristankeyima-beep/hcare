# 代码节点出入参说明：格式化普通饮食建议groups

对应代码：`代码-格式化普通饮食建议groups.py`

## 这个节点做什么

放在“节点3-1：生成普通饮食建议groups”LLM 之后，把 LLM 输出的普通饮食建议 `groups/items` 解析、归一和兜底为后续节点可稳定引用的 JSON 字符串。

该节点只做结构格式化和轻量校验提醒，不重新生成饮食建议内容。

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `groups` | Array/Object/String | 否 | DIFY 结构化输出时优先传这个字段；可以是 groups 数组，也可以是包含 `groups` 的对象或 JSON 字符串。 |
| `text` | String | 否 | 未开启结构化输出时，传入 LLM 的整段 JSON 文本。 |
| `llmText` | String | 否 | 兼容字段，作用同 `text`。 |
| `llmOutput` | Object/String | 否 | 兼容字段，可传 LLM 原始输出对象。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `groups` | String(JSON Array) | 格式化后的普通饮食建议 groups，供节点6引用。 |
| `formattedGroupsJson` | String(JSON) | 包含顶层 `groups` 的完整 JSON 字符串，便于调试或透传。 |
| `groupsCount` | Number | 当前有效普通建议 group 数量。 |
| `itemsCount` | Number | 当前有效普通建议 item 数量。 |
| `formatWarnings` | String(JSON Array) | 格式化过程中的结构提醒。为空数组字符串表示未发现结构问题。 |

## 归一规则

- 普通建议 group 固定 `groupType=adviceList`。
- `displayStyle` 为空时兜底为 `list`。
- 普通建议 item 固定 `itemType=advice`。
- `title` 为空时兜底为“饮食建议”。
- `focusPoint` 为空时兜底为“请结合后续记录和健管师评估进一步调整。”
- `importance` 只能取 `重点执行`、`常规建议`、`补充建议`，非法值归一为 `常规建议`。
- 如果 LLM 误输出 `groupType=weeklyMealPlan`，该 group 会被跳过；7 天菜谱只允许由节点4生成。

## 校验提醒

该节点会把以下问题写入 `formatWarnings`：

- 没有解析到有效普通建议 groups。
- group 不是对象或缺少 `groupTitle`。
- item 不是对象或缺少 `content`。
- `importance` 取值非法。
- 普通建议节点误输出了 `weeklyMealPlan`。

最终严格校验仍由节点6统一完成。
