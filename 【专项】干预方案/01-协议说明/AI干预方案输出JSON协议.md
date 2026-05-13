# 干预方案 JSON 数据结构说明

## 设计目标

这份 JSON 既是大模型节点的结构化输出，也是健管师审阅修改的直接对象，同时还是 H5 页面渲染的数据源。

因此结构设计遵循三个原则：

- 层级浅，尽量不超过 3 层
- 字段语义直观，方便人工直接改
- 各干预模块复用同一套 `groups/items` 结构，降低模板渲染复杂度
- 同一层级字段集合保持稳定：不同 `groupType` 的 group、不同 `itemType` 的 item 都保留同一批字段；没有值时补空字符串、空数组或空对象，避免前端按类型处理字段缺失。

## 顶层结构

```json
{
  "planName": "健康干预方案",
  "planTitle": "个性化健康管理建议",
  "planSummary": "方案概述正文",
  "executionPoints": "执行要点正文",
  "groups": []
}
```

## 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| planName | string | 页面方案标签，如“健康干预方案” |
| planTitle | string | 页面主标题，由健管师可维护 |
| planSummary | string | 方案概述，介绍主要内容、原理和目标 |
| executionPoints | string | 执行要点，说明重点执行原则和风险提醒 |
| groups | array | 干预条目组列表 |

## groups[] 结构

```json
{
  "groupTitle": "饮食干预",
  "groupType": "adviceList",
  "groupSummary": "当前分组的简短说明",
  "displayStyle": "list",
  "dietPlanGoalLabel": "",
  "goalBasis": "",
  "items": []
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| groupTitle | string | 条目组标题，由具体方案类型动态生成，例如饮食方案可使用“主食与血糖管理”，运动方案可使用“有氧运动安排” |
| groupType | string | 分组类型，用于前端选择展示组件；默认 `adviceList` |
| groupSummary | string | 当前分组的简短说明，便于患者理解这一组要解决什么问题 |
| displayStyle | string | 展示样式建议，如 `list`、`cards`、`weeklyMealPlan`，前端可按需使用 |
| dietPlanGoalLabel | string | 饮食菜谱目标中文展示名；非菜谱分组可为空字符串 |
| goalBasis | string | 菜谱目标依据；非菜谱分组可为空字符串 |
| items | array | 当前组下的具体建议条目 |

## items[] 结构

```json
{
  "itemType": "advice",
  "title": "条目标题",
  "content": "具体建议/目标/执行方式",
  "focusPoint": "解释说明、注意事项、依据",
  "importance": "重点执行",
  "day": "",
  "dailyTotalKcal": "",
  "dailyTotalProteinG": "",
  "dailyTotalFatG": "",
  "estimatedEnergyDeficitKcal": "",
  "meals": []
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| itemType | string | 条目类型；普通建议为 `advice`，每日菜谱为 `dailyMealPlan` |
| title | string | 条目标题，适用于需要卡片化展示的内容 |
| content | string | 患者直接阅读的行动建议、控制目标或监测安排 |
| focusPoint | string | 关注点、原因解释、注意事项、个体化边界 |
| importance | string | 重要程度枚举：重点执行 / 常规建议 / 补充建议 |
| day | number/string | 菜谱第几天；普通建议为空字符串 |
| dailyTotalKcal | number/string | 当日总热量；普通建议为空字符串 |
| dailyTotalProteinG | number/string | 当日总蛋白质；普通建议为空字符串 |
| dailyTotalFatG | number/string | 当日总脂肪；普通建议为空字符串 |
| estimatedEnergyDeficitKcal | number/string | 预计热量缺口；不适用时为空字符串 |
| meals | array | 菜谱餐次列表；普通建议为空数组 |

## groupType 建议

| groupType | 适用场景 | 前端展示建议 |
| --- | --- | --- |
| adviceList | 普通干预建议列表 | 列表或卡片 |
| weeklyMealPlan | 最近 7 天饮食执行菜谱 | 按天折叠、表格或日历卡片 |
| monitoringPlan | 指标监测、复盘、反馈安排 | 时间线或清单 |

## weeklyMealPlan 扩展结构

饮食方案需要输出 7 天菜谱时，不新增顶层字段，而是在 `groups[]` 中新增一个 `groupType=weeklyMealPlan` 的分组。

```json
{
  "groupTitle": "最近7天饮食执行菜谱",
  "groupType": "weeklyMealPlan",
  "groupSummary": "按减重控糖目标安排7天三餐，日均约1600千卡。",
  "displayStyle": "weeklyMealPlan",
  "dietPlanGoalLabel": "减重控糖",
  "goalBasis": "方案目标明确要求控制血糖、减重；患者体重偏高且外卖频率较高。",
  "items": [
    {
      "itemType": "dailyMealPlan",
      "day": 1,
      "title": "第1天",
      "content": "控糖减重基础日",
      "focusPoint": "全天约1580千卡，预计形成约400千卡热量缺口。",
      "importance": "重点执行",
      "dailyTotalKcal": 1580,
      "dailyTotalProteinG": 86,
      "dailyTotalFatG": 45,
      "estimatedEnergyDeficitKcal": 400,
      "meals": [
        {
          "mealName": "早餐",
          "mealTotalKcal": 420,
          "mealTotalProteinG": 23,
          "mealTotalFatG": 12,
          "foods": [
            {
              "name": "燕麦",
              "amountG": 40,
              "kcal": 150,
              "proteinG": 5,
              "fatG": 3
            }
          ]
        },
        {
          "mealName": "午餐",
          "mealTotalKcal": 620,
          "mealTotalProteinG": 38,
          "mealTotalFatG": 18,
          "foods": [
            {
              "name": "糙米饭",
              "amountG": 120,
              "kcal": 140,
              "proteinG": 3,
              "fatG": 1
            }
          ]
        },
        {
          "mealName": "晚餐",
          "mealTotalKcal": 540,
          "mealTotalProteinG": 25,
          "mealTotalFatG": 15,
          "foods": [
            {
              "name": "清蒸鱼",
              "amountG": 120,
              "kcal": 150,
              "proteinG": 25,
              "fatG": 5
            }
          ]
        }
      ]
    }
  ]
}
```

### 菜谱目标展示建议

最终 JSON 只输出面向健管师和用户可读的 `dietPlanGoalLabel`，不输出内部枚举字段。

| 字段 | 说明 |
| --- | --- |
| dietPlanGoalLabel | 菜谱目标的中文展示名，例如 `减重控糖`、`控糖`、`术后康复` |
| goalBasis | 为什么按这个目标生成菜谱，使用面向健管师可读的自然语言 |

工作流内部可以在节点2使用枚举识别饮食方案目的，但该枚举不进入最终成果物。若目标不清楚，`dietPlanGoalLabel` 应使用“一般健康管理”，并在 `goalBasis` 中说明“本次方案目标未明确具体饮食目的，按一般慢病饮食管理生成保守菜谱”。

## 示例

```json
{
  "planName": "健康干预方案",
  "planTitle": "个性化健康管理建议",
  "planSummary": "本方案围绕糖尿病合并血压偏高管理，从饮食、运动、控制目标和监测四个方面帮助患者提升自我管理能力。",
  "executionPoints": "优先落实重点执行条目；如连续指标异常或明显不适，应及时联系医生或健管师。",
  "groups": [
    {
      "groupTitle": "饮食干预",
      "groupType": "adviceList",
      "groupSummary": "饮食调整的核心建议。",
      "displayStyle": "list",
      "dietPlanGoalLabel": "",
      "goalBasis": "",
      "items": [
        {
          "itemType": "advice",
          "day": "",
          "title": "",
          "content": "每餐主食控制在1拳左右，优先选择全谷物，减少甜饮料和甜点。",
          "focusPoint": "重点降低餐后血糖波动；如近期有低血糖风险，应先确认调整幅度。",
          "importance": "重点执行",
          "dailyTotalKcal": "",
          "dailyTotalProteinG": "",
          "dailyTotalFatG": "",
          "estimatedEnergyDeficitKcal": "",
          "meals": []
        }
      ]
    }
  ]
}
```

## 不建议加入的结构

- 不建议在 `items` 下继续增加多层 `subItems` 嵌套。
- 不建议为饮食/运动/监测分别设计完全不同的数据对象结构。
- 不建议把复杂规则表达式、内部推理链路或大段模型解释写进 JSON。
