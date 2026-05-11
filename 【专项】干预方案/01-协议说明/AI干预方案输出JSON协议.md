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
  "group_type": "advice_list",
  "group_summary": "当前分组的简短说明",
  "display_style": "list",
  "items": []
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| group_title | string | 条目组标题，由具体方案类型动态生成，例如饮食方案可使用“主食与血糖管理”，运动方案可使用“有氧运动安排” |
| group_type | string | 分组类型，用于前端选择展示组件；默认 `advice_list` |
| group_summary | string | 当前分组的简短说明，便于患者理解这一组要解决什么问题 |
| display_style | string | 展示样式建议，如 `list`、`cards`、`weekly_meal_plan`，前端可按需使用 |
| items | array | 当前组下的具体建议条目 |

## items[] 结构

```json
{
  "item_type": "advice",
  "title": "条目标题",
  "content": "具体建议/目标/执行方式",
  "focus_point": "解释说明、注意事项、依据",
  "importance": "重点执行"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| item_type | string | 条目类型；普通建议为 `advice`，每日菜谱为 `daily_meal_plan` |
| title | string | 条目标题，适用于需要卡片化展示的内容 |
| content | string | 患者直接阅读的行动建议、控制目标或监测安排 |
| focus_point | string | 关注点、原因解释、注意事项、个体化边界 |
| importance | string | 重要程度枚举：重点执行 / 常规建议 / 补充建议 |

## group_type 建议

| group_type | 适用场景 | 前端展示建议 |
| --- | --- | --- |
| advice_list | 普通干预建议列表 | 列表或卡片 |
| weekly_meal_plan | 最近 7 天饮食执行菜谱 | 按天折叠、表格或日历卡片 |
| monitoring_plan | 指标监测、复盘、反馈安排 | 时间线或清单 |

## weekly_meal_plan 扩展结构

饮食方案需要输出 7 天菜谱时，不新增顶层字段，而是在 `groups[]` 中新增一个 `group_type=weekly_meal_plan` 的分组。

```json
{
  "group_title": "最近7天饮食执行菜谱",
  "group_type": "weekly_meal_plan",
  "group_summary": "按减重控糖目标安排7天三餐，日均约1600千卡。",
  "display_style": "weekly_meal_plan",
  "diet_plan_goal_label": "减重控糖",
  "goal_basis": "方案目标明确要求控制血糖、减重；患者体重偏高且外卖频率较高。",
  "items": [
    {
      "item_type": "daily_meal_plan",
      "day": 1,
      "title": "第1天",
      "content": "控糖减重基础日",
      "focus_point": "全天约1580千卡，预计形成约400千卡热量缺口。",
      "importance": "重点执行",
      "daily_total_kcal": 1580,
      "daily_total_protein_g": 86,
      "daily_total_fat_g": 45,
      "estimated_energy_deficit_kcal": 400,
      "meals": [
        {
          "meal_name": "早餐",
          "meal_total_kcal": 420,
          "meal_total_protein_g": 23,
          "meal_total_fat_g": 12,
          "foods": [
            {
              "name": "燕麦",
              "amount_g": 40,
              "kcal": 150,
              "protein_g": 5,
              "fat_g": 3
            }
          ]
        },
        {
          "meal_name": "午餐",
          "meal_total_kcal": 620,
          "meal_total_protein_g": 38,
          "meal_total_fat_g": 18,
          "foods": [
            {
              "name": "糙米饭",
              "amount_g": 120,
              "kcal": 140,
              "protein_g": 3,
              "fat_g": 1
            }
          ]
        },
        {
          "meal_name": "晚餐",
          "meal_total_kcal": 540,
          "meal_total_protein_g": 25,
          "meal_total_fat_g": 15,
          "foods": [
            {
              "name": "清蒸鱼",
              "amount_g": 120,
              "kcal": 150,
              "protein_g": 25,
              "fat_g": 5
            }
          ]
        }
      ]
    }
  ]
}
```

### 菜谱目标展示建议

最终 JSON 只输出面向健管师和用户可读的 `diet_plan_goal_label`，不输出内部枚举字段。

| 字段 | 说明 |
| --- | --- |
| diet_plan_goal_label | 菜谱目标的中文展示名，例如 `减重控糖`、`控糖`、`术后康复` |
| goal_basis | 为什么按这个目标生成菜谱，使用面向健管师可读的自然语言 |

工作流内部可以在节点2使用枚举识别饮食方案目的，但该枚举不进入最终成果物。若目标不清楚，`diet_plan_goal_label` 应使用“一般健康管理”，并在 `goal_basis` 中说明“本次方案目标未明确具体饮食目的，按一般慢病饮食管理生成保守菜谱”。

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
      "group_type": "advice_list",
      "items": [
        {
          "item_type": "advice",
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
