# 代码节点出入参说明：保护素材摘要 LLM 出参

对应代码：`代码-保护素材摘要LLM出参.py`

## 这个节点做什么

保护节点2素材摘要 LLM 的输出格式，确保后续节点稳定拿到 `materialSummaryBundle`。

它会：

- 解析 LLM 返回的 JSON 对象或包在文本中的 JSON 对象
- 兜底补齐 `medicalGoalSummary`、`sportExecutionSummary`、`safetyBoundarySummary`
- 汇总输出 `materialSummaryBundle`
- 原样带出 `planGoalAndRequirements` 和 `extraSupplement`

当前 Dify yml 实际绑定方式：

- `llmOutput: String(JSON) <= 运动方案素材摘要整理.text`

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `llmOutput` | String(JSON) | 是 | 当前 yml 实际绑定字段，传入节点2素材摘要 LLM 的整段 JSON 文本。 |
| `medicalGoalSummary` | String | 否 | 兼容散字段；当前 yml 不按该字段绑定。 |
| `sportExecutionSummary` | String | 否 | 兼容散字段；当前 yml 不按该字段绑定。 |
| `safetyBoundarySummary` | String | 否 | 兼容散字段；当前 yml 不按该字段绑定。 |
| `planGoalAndRequirements` | String | 否 | 节点1原样带出的方案目标。 |
| `extraSupplement` | String | 否 | 节点1原样带出的补充信息。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `planGoalAndRequirements` | String | 原样带出。 |
| `extraSupplement` | String | 原样带出。 |
| `medicalGoalSummary` | String | 疾病边界 + 指标目标摘要。 |
| `sportExecutionSummary` | String | 运动能力 + 执行问题摘要。 |
| `safetyBoundarySummary` | String | 安全风险 + 运动边界摘要。 |
| `materialSummaryBundle` | Object | 三类摘要汇总结果。 |
| `materialSummaryBundleText` | String | `materialSummaryBundle` 的 JSON 字符串版本。 |
| `summaryMissingFields` | Array<String> | 使用兜底文案的摘要字段。 |
| `summaryMissingFieldsCount` | Number | 使用兜底文案的摘要字段数量。 |

## 入参示例

```json
{
  "llmOutput": "{\"medicalGoalSummary\":\"患者为2型糖尿病...\",\"sportExecutionSummary\":\"日常步数偏少...\",\"safetyBoundarySummary\":\"运动前后需关注低血糖...\"}",
  "planGoalAndRequirements": "生成控糖减重运动方案",
  "extraSupplement": "患者夜班较多"
}
```

## 出参示例

```json
{
  "planGoalAndRequirements": "生成控糖减重运动方案",
  "extraSupplement": "患者夜班较多",
  "medicalGoalSummary": "患者为2型糖尿病...",
  "sportExecutionSummary": "日常步数偏少...",
  "safetyBoundarySummary": "运动前后需关注低血糖...",
  "materialSummaryBundle": {
    "medicalGoalSummary": "患者为2型糖尿病...",
    "sportExecutionSummary": "日常步数偏少...",
    "safetyBoundarySummary": "运动前后需关注低血糖..."
  },
  "materialSummaryBundleText": "{\"medicalGoalSummary\":\"患者为2型糖尿病...\",\"sportExecutionSummary\":\"日常步数偏少...\",\"safetyBoundarySummary\":\"运动前后需关注低血糖...\"}",
  "summaryMissingFields": [],
  "summaryMissingFieldsCount": 0
}
```
