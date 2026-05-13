# AI干预方案入参说明

## 使用场景

本文档用于说明 AI 干预方案工作流需要的外部入参结构。工作流建议一次性接收一个 JSON 对象，顶层包含方案类型、方案要求和患者上下文数据。

| 入参字段 | 中文含义 | 数据范围 |
| --- | --- | --- |
| `planType` | 方案类型 | 前端页面或调用方传入；`diet` 代表饮食方案，`sport` 代表运动方案 |
| `planGoalAndRequirements` | 方案目标和额外要求 | 前端页面录入 |
| `extraSupplement` | 额外补充信息 | 前端页面录入 |
| `basicProfile` | 基础档案 | 当前 |
| `diseaseProfile` | 专病档案 | 当前 |
| `followupRecordsLast1y` | 随访记录 | 最近 1 年 |
| `metricRecordsLast1y` | 指标记录 | 最近 1 年 |
| `dietRecordsLast1y` | 饮食记录 | 最近 1 年 |
| `exerciseRecordsLast1y` | 运动记录 | 最近 1 年 |
| `medPickupRecords1y` | 取药记录 | 最近 1 年 |
| `activeControlGoals` | 当前生效控制目标 | 当前生效 |

## 完整入参示例

```json
{
  "planType": "diet",
  "planGoalAndRequirements": "希望生成一个控制血糖、减重、改善饮食和运动习惯的个性化干预方案；语言通俗，重点突出可执行动作。",
  "extraSupplement": "患者近期夜班较多，作息不规律，外卖频率较高，希望方案尽量适配夜班场景。",
  "basicProfile": {
    "demographics": {
      "gender": "男",
      "age": 62
    },
    "healthInfo": {
      "currentDiseases": [
        {
          "category": "糖尿病",
          "name": "糖尿病"
        },
        {
          "category": "高血脂 高脂血症",
          "name": "混合性高脂血症"
        }
      ],
      "otherConditionInput": "",
      "familyHistory": [
        "否认家族遗传传染史"
      ],
      "pastHistory": []
    },
    "lifestyle": {
      "foodAllergies": [
        "无"
      ],
      "dietHabit": "荤素均衡",
      "dietTaste": "适中",
      "mainMealsPerDay": 3,
      "dailyStapleFoods": [
        "粗粮或杂粮"
      ],
      "laborIntensity": "轻体力劳动",
      "dailySteps": 3000,
      "exerciseMethods": {
        "lowIntensity": [
          "慢走"
        ],
        "mediumIntensity": [
          "慢跑"
        ],
        "highIntensity": []
      },
      "exerciseTime": "请选择",
      "exerciseDuration": "请选择",
      "exerciseFrequency": "请选择",
      "smokingHistory": "无",
      "drinkingHistory": "无"
    }
  },
  "diseaseProfile": {
    "diabetesProfile": {
      "diabetesType": "2型糖尿病",
      "diagnosisTime": "2019-05-15",
      "symptoms": [
        "多饮",
        "多食",
        "多尿"
      ],
      "hypoglycemiaHistory": "否",
      "complications": [
        "高血压",
        "周围血管病变"
      ],
      "otherComplications": "",
      "acuteComplications": [],
      "remark": ""
    },
    "hypertensionProfile": {
      "hypertensionType": "原发性高血压",
      "diagnosisTime": "2020-01-01",
      "grade": "正常",
      "stage": "请选择",
      "prematureCvdFamilyHistory": "请选择",
      "complications": [
        "高血压",
        "肥胖症"
      ],
      "otherComplications": "",
      "remark": ""
    },
    "obesityProfile": {
      "bodySigns": {
        "bodyFatRatePercent": 40.1,
        "bodyFatMassKg": 38.6,
        "muscleMassKg": 52.3,
        "visceralFatAreaCm2": 131,
        "visceralFatGrade": 15,
        "waistCm": 107
      },
      "obesityHistory": {
        "startAge": 26,
        "years": 10,
        "maxWeightKg": 100,
        "ageAtMaxWeight": 36,
        "causes": [
          "饮食不合理、运动少",
          "学习工作劳累、压力大"
        ]
      },
      "weightLossHistory": {
        "hasHistory": true,
        "methods": [
          {
            "method": "节食代餐",
            "maxWeightLossKg": 0,
            "rebounded": true
          },
          {
            "method": "药物",
            "maxWeightLossKg": 5,
            "rebounded": true
          }
        ],
        "remark": ""
      },
      "currentDiet": {
        "breakfast": "不吃或包子/油条、豆浆",
        "lunch": "医院食堂",
        "dinner": "面食+菜类/卤外卖类",
        "lateNightSnack": "偶尔",
        "dietProblem": "外卖较多、护工夜班熬夜、饮食不规律"
      },
      "weightLossGoal": {
        "targetWeightBelowKg": null,
        "stageWeightLossKg": null,
        "bodyFatPercent": null
      }
    }
  },
  "followupRecordsLast1y": [
    {
      "followupType": "糖尿病日常随访",
      "completedAt": "2025-12-06 00:00:00",
      "lifestyleStatus": {
        "stapleFoodGPerDay": 300,
        "cigarettesPerDay": null,
        "waterMlPerDay": null,
        "exerciseFrequencyPerWeek": 1,
        "exerciseMinutesPerTime": 30
      },
      "advice": {
        "currentProblems": "患者近期空腹血糖控制不稳，餐后未测，血压平稳，体重偏高",
        "improvementMeasures": "建议定期监测血糖，合理搭配饮食，适度运动，规律用药，控制体重，定期复查糖化和血脂",
        "expectedGoal": ""
      }
    },
    {
      "followupType": "高血压随访",
      "completedAt": "2025-10-28 15:16:00",
      "lifestyleStatus": {
        "stapleFoodGPerDay": 280,
        "cigarettesPerDay": 0,
        "waterMlPerDay": null,
        "exerciseFrequencyPerWeek": 3,
        "exerciseMinutesPerTime": 30
      },
      "advice": {
        "currentProblems": "体重偏高，需继续关注血压与血糖波动",
        "improvementMeasures": "建议限盐、规律运动、按时服药并记录家庭血压",
        "expectedGoal": ""
      }
    }
  ],
  "metricRecordsLast1y": [
    {
      "measuredAt": "2026-01-14 09:15:00",
      "metricName": "身高",
      "unit": "cm",
      "value": 180
    },
    {
      "measuredAt": "2026-01-14 09:15:00",
      "metricName": "体重",
      "unit": "kg",
      "value": 83.4
    },
    {
      "measuredAt": "2025-11-28 15:01:00",
      "metricName": "空腹血糖",
      "unit": "mmol/L",
      "value": 4.6
    },
    {
      "measuredAt": "2025-11-20 22:00:00",
      "metricName": "晚餐后血糖",
      "unit": "mmol/L",
      "value": 19.5
    },
    {
      "measuredAt": "2025-08-29 16:49:00",
      "metricName": "糖化血红蛋白",
      "unit": "%",
      "value": 5.0
    },
    {
      "measuredAt": "2025-10-28 18:04:00",
      "metricName": "总胆固醇",
      "unit": "mmol/L",
      "value": 6.5
    },
    {
      "measuredAt": "2025-10-28 15:16:00",
      "metricName": "起床血压",
      "unit": "mmHg",
      "value": "150/100"
    }
  ],
  "dietRecordsLast1y": [
    {
      "mealTime": "2026-04-01 08:00:00",
      "mealPeriod": "早餐",
      "foodName": "米饭",
      "intakeGrams": 100,
      "caloriesKcal": 116,
      "proteinG": 2.6,
      "carbohydrateG": 25.9,
      "fatG": 0.3
    },
    {
      "mealTime": "2026-04-01 12:30:00",
      "mealPeriod": "午餐",
      "foodName": "鸡胸肉",
      "intakeGrams": 120,
      "caloriesKcal": 160,
      "proteinG": 31.0,
      "carbohydrateG": 0,
      "fatG": 3.6
    }
  ],
  "exerciseRecordsLast1y": [
    {
      "exerciseTime": "2026-04-01 19:00:00",
      "exerciseItem": "慢走",
      "durationMinutes": 30,
      "caloriesKcal": 120
    }
  ],
  "medPickupRecords1y": [
    {
      "drugName": "阿托伐他汀钙片",
      "specification": "20mg*14片",
      "usage": "口服",
      "frequency": "1/日(8am)",
      "singleDose": "20.0mg",
      "medicationTime": "2024-05-19",
      "source": "医院药品处方同步"
    },
    {
      "drugName": "吡格列酮二甲双胍片",
      "specification": "30片",
      "usage": "口服",
      "frequency": "2/日(8am-4pm)",
      "singleDose": "500.0mg",
      "medicationTime": "2024-05-19",
      "source": "医院药品处方同步"
    }
  ],
  "activeControlGoals": [
    {
      "metricName": "空腹血糖",
      "lowerBound": {
        "value": 4.4,
        "inclusive": false
      },
      "upperBound": {
        "value": 7,
        "inclusive": false
      }
    },
    {
      "metricName": "餐后血糖",
      "lowerBound": {
        "value": 4.4,
        "inclusive": false
      },
      "upperBound": {
        "value": 10,
        "inclusive": false
      }
    }
  ]
}
```

## 关键说明

- `planType` 是总入口路由字段。`diet` 进入饮食方案工程，`sport` 进入运动方案工程；如果后续新增睡眠、用药、监测等专题，也应继续扩展该字段。
- 入参字段建议全部使用驼峰命名；饮食方案驼峰版节点1会兼容对象/数组内部仍为下划线字段的 JSON 字符串，并递归归一为驼峰字段，但上游接口最好直接按本文档传驼峰字段。
- 所有字段值建议直接传中文，便于模型生成中文干预方案。
- 时间字段建议统一使用 `YYYY-MM-DD HH:mm:ss`；仅日期字段可使用 `YYYY-MM-DD`。
- 最近一年数据建议只传已完成、已确认的数据，避免草稿或未完成记录干扰模型判断。
- `metricRecordsLast1y` 使用统一指标记录结构，不按指标单独拆顶层字段。
- 血压可先使用字符串格式，例如 `"150/100"`；如果后续接口支持，也可以拆成收缩压和舒张压两个数值字段。
- 控制目标中 `inclusive=false` 表示不包含边界，例如截图中的 `> 4.4`、`< 7`。
- 未采集或无数据字段建议传 `null`、空字符串或空数组，保持字段结构稳定。

## 与字段清单的对应关系

字段路径以 JSON 路径为准。例如：

| JSON 字段路径 | 中文含义 |
| --- | --- |
| `planType` | 方案类型，`diet` 或 `sport` |
| `planGoalAndRequirements` | 方案目标和额外要求 |
| `extraSupplement` | 额外补充信息 |
| `basicProfile.demographics.gender` | 性别 |
| `basicProfile.demographics.age` | 年龄 |
| `basicProfile.healthInfo.currentDiseases[].name` | 现有疾病名称 |
| `diseaseProfile.diabetesProfile.diabetesType` | 糖尿病类型 |
| `diseaseProfile.obesityProfile.bodySigns.waistCm` | 腰围 |
| `followupRecordsLast1y[].lifestyleStatus.stapleFoodGPerDay` | 随访中的主食摄入量 |
| `metricRecordsLast1y[].metricName` | 指标名称 |
| `dietRecordsLast1y[].caloriesKcal` | 摄入热量 |
| `exerciseRecordsLast1y[].durationMinutes` | 运动时长 |
| `medPickupRecords1y[].drugName` | 药品名称 |
| `activeControlGoals[].lowerBound.inclusive` | 目标下限是否包含边界 |
