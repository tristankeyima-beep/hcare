# 代码节点出入参说明：保护分组与 items LLM 出参

对应代码：`代码-保护分组与itemsLLM出参.py`

## 这个节点做什么

保护节点3 LLM 的输出格式，确保后续节点稳定拿到 `groupPlan` 和 `groups`。

它会：

- 解析 LLM 返回的 JSON 对象或包在文本中的 JSON 对象
- 归一化 `groupPlan`
- 归一化 `groups/items`，补齐 group 和 item 同层字段
- 校正非法 `importance`
- 按 `groupPlan` 顺序排序 groups

当前 Dify yml 实际绑定方式：

- `llmOutput: String(JSON) <= 方案内容分组并生成运动方案.text`

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `llmOutput` | String(JSON) | 是 | 当前 yml 实际绑定字段，传入节点3 LLM 的整段 JSON 文本。 |
| `llmText` | String(JSON) | 否 | 兼容字段；当 `llmOutput` 为空时读取该字段。 |
| `groupPlan` | String(JSON Array) | 否 | 兼容散字段；当前 yml 不按该字段绑定。 |
| `groups` | String(JSON Array) | 否 | 兼容散字段；当前 yml 不按该字段绑定。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `groupPlan` | Array<Object> | 归一化后的分组规划。当前 yml 后续实际传 `groupPlanText`。 |
| `groupPlanText` | String | `groupPlan` 的 JSON 字符串版本。 |
| `groups` | Array<Object> | 归一化后的最终方案条目分组。当前 yml 后续实际传 `groupsText`。 |
| `groupsText` | String | `groups` 的 JSON 字符串版本。 |
| `groupPlanCount` | Number | 分组规划数量。 |
| `groupsCount` | Number | 有效 groups 数量。 |
| `validationWarnings` | Array<String> | 非阻断性格式警告。 |
| `validationWarningsCount` | Number | 非阻断性格式警告数量。 |

## 出参结构约束

- 每个 group 都会包含：`groupTitle`、`groupType`、`groupSummary`、`displayStyle`、`dietPlanGoalLabel`、`goalBasis`、`items`
- 每个 item 都会包含：`itemType`、`day`、`title`、`content`、`focusPoint`、`importance`、`dailyTotalKcal`、`dailyTotalProteinG`、`dailyTotalFatG`、`estimatedEnergyDeficitKcal`、`meals`
- `importance` 非法时自动归一为 `常规建议`

## 入参示例

```json
{
  "llmText": "{\"groupPlan\":[{\"groupTitle\":\"有氧运动安排\",\"groupFocus\":\"运动方式、频率和强度\"}],\"groups\":[{\"groupTitle\":\"有氧运动安排\",\"items\":[{\"content\":\"每周5天快走，每次20-30分钟。\",\"focusPoint\":\"从低强度开始。\",\"importance\":\"重点执行\"}]}]}"
}
```

## 出参示例

```json
{
  "groupPlan": [
    {
      "groupTitle": "有氧运动安排",
      "groupFocus": "运动方式、频率和强度"
    }
  ],
  "groups": [
    {
      "groupTitle": "有氧运动安排",
      "groupType": "adviceList",
      "groupSummary": "运动方式、频率和强度",
      "displayStyle": "list",
      "dietPlanGoalLabel": "",
      "goalBasis": "",
      "items": [
        {
          "itemType": "advice",
          "day": "",
          "title": "",
          "content": "每周5天快走，每次20-30分钟。",
          "focusPoint": "从低强度开始。",
          "importance": "重点执行",
          "dailyTotalKcal": "",
          "dailyTotalProteinG": "",
          "dailyTotalFatG": "",
          "estimatedEnergyDeficitKcal": "",
          "meals": []
        }
      ]
    }
  ],
  "groupPlanCount": 1,
  "groupsCount": 1,
  "validationWarnings": [],
  "validationWarningsCount": 0
}
```
