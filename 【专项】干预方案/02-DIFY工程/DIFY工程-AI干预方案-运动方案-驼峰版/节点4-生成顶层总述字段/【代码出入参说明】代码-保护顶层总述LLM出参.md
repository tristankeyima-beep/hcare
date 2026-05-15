# 代码节点出入参说明：保护顶层总述 LLM 出参

对应代码：`代码-保护顶层总述LLM出参.py`

## 这个节点做什么

保护节点4顶层总述 LLM 的输出格式，确保节点5稳定拿到 `planHeader`。

它会：

- 解析 LLM 返回的 JSON 对象或包在文本中的 JSON 对象
- 补齐 `planName`、`planTitle`、`planSummary`、`executionPoints`
- 输出对象版 `planHeader` 和字符串版 `planHeaderText`

## 入参

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `llmOutput` | String 或 Object | 否 | 节点4 LLM 的完整输出，期望包含顶层总述字段。 |
| `llmText` | String 或 Object | 否 | 兼容 DIFY 节点实际传入字段；当 `llmOutput` 为空时读取该字段。 |
| `planName` | String | 否 | 如果 DIFY 已将 LLM 结构化字段拆出，可直接传入该字段。 |
| `planTitle` | String | 否 | 如果 DIFY 已将 LLM 结构化字段拆出，可直接传入该字段。 |
| `planSummary` | String | 否 | 如果 DIFY 已将 LLM 结构化字段拆出，可直接传入该字段。 |
| `executionPoints` | String | 否 | 如果 DIFY 已将 LLM 结构化字段拆出，可直接传入该字段。 |

## 出参

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `planName` | String | 方案名称。 |
| `planTitle` | String | 方案标题。 |
| `planSummary` | String | 方案摘要。 |
| `executionPoints` | String | 执行要点。 |
| `planHeader` | Object | 顶层总述字段对象。 |
| `planHeaderText` | String | `planHeader` 的 JSON 字符串版本。 |
| `fallbackFields` | Array<String> | 使用默认兜底值的字段。 |
| `fallbackFieldsCount` | Number | 使用默认兜底值的字段数量。 |

## 入参示例

```json
{
  "llmText": "{\"planName\":\"运动健康处方\",\"planTitle\":\"个性化运动管理建议\",\"planSummary\":\"围绕有氧运动和安全监测提供建议。\",\"executionPoints\":\"循序渐进；出现不适及时停止并联系医生或健管师。\"}"
}
```

## 出参示例

```json
{
  "planName": "运动健康处方",
  "planTitle": "个性化运动管理建议",
  "planSummary": "围绕有氧运动和安全监测提供建议。",
  "executionPoints": "循序渐进；出现不适及时停止并联系医生或健管师。",
  "planHeader": {
    "planName": "运动健康处方",
    "planTitle": "个性化运动管理建议",
    "planSummary": "围绕有氧运动和安全监测提供建议。",
    "executionPoints": "循序渐进；出现不适及时停止并联系医生或健管师。"
  },
  "planHeaderText": "{\"planName\":\"运动健康处方\",\"planTitle\":\"个性化运动管理建议\",\"planSummary\":\"围绕有氧运动和安全监测提供建议。\",\"executionPoints\":\"循序渐进；出现不适及时停止并联系医生或健管师。\"}",
  "fallbackFields": [],
  "fallbackFieldsCount": 0
}
```
