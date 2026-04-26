# 干预方案 JSON 数据结构说明

## 设计目标

这份 JSON 既是大模型节点的结构化输出，也是健管师审阅修改的直接对象，同时还是 H5 页面渲染的数据源。

因此结构设计遵循三个原则：

- 层级浅，尽量不超过 3 层
- 字段语义直观，方便人工直接改
- 各干预模块复用同一套 `groups/items` 结构，降低模板渲染复杂度

## 顶层结构

```json
{
  "plan_name": "健康干预方案",
  "plan_title": "个性化健康管理建议",
  "plan_summary": "方案概述正文",
  "execution_points": "执行要点正文",
  "groups": []
}
```

## 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| plan_name | string | 页面方案标签，如“健康干预方案” |
| plan_title | string | 页面主标题，由健管师可维护 |
| plan_summary | string | 方案概述，介绍主要内容、原理和目标 |
| execution_points | string | 执行要点，说明重点执行原则和风险提醒 |
| groups | array | 干预条目组列表 |

## groups[] 结构

```json
{
  "group_title": "饮食干预",
  "items": []
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| group_title | string | 条目组标题，建议使用饮食干预/运动干预/控制目标/监测方案 |
| items | array | 当前组下的具体建议条目 |

## items[] 结构

```json
{
  "content": "具体建议/目标/执行方式",
  "focus_point": "解释说明、注意事项、依据",
  "importance": "重点执行"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| content | string | 患者直接阅读的行动建议、控制目标或监测安排 |
| focus_point | string | 关注点、原因解释、注意事项、个体化边界 |
| importance | string | 重要程度枚举：重点执行 / 常规建议 / 补充建议 |

## 示例

```json
{
  "plan_name": "健康干预方案",
  "plan_title": "个性化健康管理建议",
  "plan_summary": "本方案围绕糖尿病合并血压偏高管理，从饮食、运动、控制目标和监测四个方面帮助患者提升自我管理能力。",
  "execution_points": "优先落实重点执行条目；如连续指标异常或明显不适，应及时联系医生或健管师。",
  "groups": [
    {
      "group_title": "饮食干预",
      "items": [
        {
          "content": "每餐主食控制在1拳左右，优先选择全谷物，减少甜饮料和甜点。",
          "focus_point": "重点降低餐后血糖波动；如近期有低血糖风险，应先确认调整幅度。",
          "importance": "重点执行"
        }
      ]
    }
  ]
}
```

## 不建议加入的结构

- 不建议在 `items` 下继续增加多层 `sub_items` 嵌套。
- 不建议为饮食/运动/监测分别设计完全不同的数据对象结构。
- 不建议把复杂规则表达式、内部推理链路或大段模型解释写进 JSON。
