# AI干预方案入参说明

## 使用场景

本文档用于说明 AI 干预方案工作流需要的外部入参结构。工作流建议一次性接收一个 JSON 对象，顶层包含方案类型、方案要求和患者上下文数据。

| 入参字段 | 中文含义 | 数据范围 |
| --- | --- | --- |
| `plan_type` | 方案类型 | 前端页面或调用方传入；`diet` 代表饮食方案，`sport` 代表运动方案 |
| `plan_goal_and_requirements` | 方案目标和额外要求 | 前端页面录入 |
| `extra_supplement` | 额外补充信息 | 前端页面录入 |
| `basic_profile` | 基础档案 | 当前 |
| `disease_profile` | 专病档案 | 当前 |
| `followup_records_last_1y` | 随访记录 | 最近 1 年 |
| `metric_records_last_1y` | 指标记录 | 最近 1 年 |
| `diet_records_last_1y` | 饮食记录 | 最近 1 年 |
| `exercise_records_last_1y` | 运动记录 | 最近 1 年 |
| `medication_pickup_records_last_1y` | 取药记录 | 最近 1 年 |
| `active_control_goals` | 当前生效控制目标 | 当前生效 |

## 完整入参示例

```json
{
  "plan_type": "diet",
  "plan_goal_and_requirements": "希望生成一个控制血糖、减重、改善饮食和运动习惯的个性化干预方案；语言通俗，重点突出可执行动作。",
  "extra_supplement": "患者近期夜班较多，作息不规律，外卖频率较高，希望方案尽量适配夜班场景。",
  "basic_profile": {
    "demographics": {
      "gender": "男",
      "age": 62
    },
    "health_info": {
      "current_diseases": [
        {
          "category": "糖尿病",
          "name": "糖尿病"
        },
        {
          "category": "高血脂 高脂血症",
          "name": "混合性高脂血症"
        }
      ],
      "other_condition_input": "",
      "family_history": [
        "否认家族遗传传染史"
      ],
      "past_history": []
    },
    "lifestyle": {
      "food_allergies": [
        "无"
      ],
      "diet_habit": "荤素均衡",
      "diet_taste": "适中",
      "main_meals_per_day": 3,
      "daily_staple_foods": [
        "粗粮或杂粮"
      ],
      "labor_intensity": "轻体力劳动",
      "daily_steps": 3000,
      "exercise_methods": {
        "low_intensity": [
          "慢走"
        ],
        "medium_intensity": [
          "慢跑"
        ],
        "high_intensity": []
      },
      "exercise_time": "请选择",
      "exercise_duration": "请选择",
      "exercise_frequency": "请选择",
      "smoking_history": "无",
      "drinking_history": "无"
    }
  },
  "disease_profile": {
    "diabetes_profile": {
      "diabetes_type": "2型糖尿病",
      "diagnosis_time": "2019-05-15",
      "symptoms": [
        "多饮",
        "多食",
        "多尿"
      ],
      "hypoglycemia_history": "否",
      "complications": [
        "高血压",
        "周围血管病变"
      ],
      "other_complications": "",
      "acute_complications": [],
      "remark": ""
    },
    "hypertension_profile": {
      "hypertension_type": "原发性高血压",
      "diagnosis_time": "2020-01-01",
      "grade": "正常",
      "stage": "请选择",
      "premature_cvd_family_history": "请选择",
      "complications": [
        "高血压",
        "肥胖症"
      ],
      "other_complications": "",
      "remark": ""
    },
    "obesity_profile": {
      "body_signs": {
        "body_fat_rate_percent": 40.1,
        "body_fat_mass_kg": 38.6,
        "muscle_mass_kg": 52.3,
        "visceral_fat_area_cm2": 131,
        "visceral_fat_grade": 15,
        "waist_cm": 107
      },
      "obesity_history": {
        "start_age": 26,
        "years": 10,
        "max_weight_kg": 100,
        "age_at_max_weight": 36,
        "causes": [
          "饮食不合理、运动少",
          "学习工作劳累、压力大"
        ]
      },
      "weight_loss_history": {
        "has_history": true,
        "methods": [
          {
            "method": "节食代餐",
            "max_weight_loss_kg": 0,
            "rebounded": true
          },
          {
            "method": "药物",
            "max_weight_loss_kg": 5,
            "rebounded": true
          }
        ],
        "remark": ""
      },
      "current_diet": {
        "breakfast": "不吃或包子/油条、豆浆",
        "lunch": "医院食堂",
        "dinner": "面食+菜类/卤外卖类",
        "late_night_snack": "偶尔",
        "diet_problem": "外卖较多、护工夜班熬夜、饮食不规律"
      },
      "weight_loss_goal": {
        "target_weight_below_kg": null,
        "stage_weight_loss_kg": null,
        "body_fat_percent": null
      }
    }
  },
  "followup_records_last_1y": [
    {
      "followup_type": "糖尿病日常随访",
      "completed_at": "2025-12-06 00:00:00",
      "lifestyle_status": {
        "staple_food_g_per_day": 300,
        "cigarettes_per_day": null,
        "water_ml_per_day": null,
        "exercise_frequency_per_week": 1,
        "exercise_minutes_per_time": 30
      },
      "advice": {
        "current_problems": "患者近期空腹血糖控制不稳，餐后未测，血压平稳，体重偏高",
        "improvement_measures": "建议定期监测血糖，合理搭配饮食，适度运动，规律用药，控制体重，定期复查糖化和血脂",
        "expected_goal": ""
      }
    },
    {
      "followup_type": "高血压随访",
      "completed_at": "2025-10-28 15:16:00",
      "lifestyle_status": {
        "staple_food_g_per_day": 280,
        "cigarettes_per_day": 0,
        "water_ml_per_day": null,
        "exercise_frequency_per_week": 3,
        "exercise_minutes_per_time": 30
      },
      "advice": {
        "current_problems": "体重偏高，需继续关注血压与血糖波动",
        "improvement_measures": "建议限盐、规律运动、按时服药并记录家庭血压",
        "expected_goal": ""
      }
    }
  ],
  "metric_records_last_1y": [
    {
      "measured_at": "2026-01-14 09:15:00",
      "metric_name": "身高",
      "unit": "cm",
      "value": 180
    },
    {
      "measured_at": "2026-01-14 09:15:00",
      "metric_name": "体重",
      "unit": "kg",
      "value": 83.4
    },
    {
      "measured_at": "2025-11-28 15:01:00",
      "metric_name": "空腹血糖",
      "unit": "mmol/L",
      "value": 4.6
    },
    {
      "measured_at": "2025-11-20 22:00:00",
      "metric_name": "晚餐后血糖",
      "unit": "mmol/L",
      "value": 19.5
    },
    {
      "measured_at": "2025-08-29 16:49:00",
      "metric_name": "糖化血红蛋白",
      "unit": "%",
      "value": 5.0
    },
    {
      "measured_at": "2025-10-28 18:04:00",
      "metric_name": "总胆固醇",
      "unit": "mmol/L",
      "value": 6.5
    },
    {
      "measured_at": "2025-10-28 15:16:00",
      "metric_name": "起床血压",
      "unit": "mmHg",
      "value": "150/100"
    }
  ],
  "diet_records_last_1y": [
    {
      "meal_time": "2026-04-01 08:00:00",
      "meal_period": "早餐",
      "food_name": "米饭",
      "intake_grams": 100,
      "calories_kcal": 116,
      "protein_g": 2.6,
      "carbohydrate_g": 25.9,
      "fat_g": 0.3
    },
    {
      "meal_time": "2026-04-01 12:30:00",
      "meal_period": "午餐",
      "food_name": "鸡胸肉",
      "intake_grams": 120,
      "calories_kcal": 160,
      "protein_g": 31.0,
      "carbohydrate_g": 0,
      "fat_g": 3.6
    }
  ],
  "exercise_records_last_1y": [
    {
      "exercise_time": "2026-04-01 19:00:00",
      "exercise_item": "慢走",
      "duration_minutes": 30,
      "calories_kcal": 120
    }
  ],
  "medication_pickup_records_last_1y": [
    {
      "drug_name": "阿托伐他汀钙片",
      "specification": "20mg*14片",
      "usage": "口服",
      "frequency": "1/日(8am)",
      "single_dose": "20.0mg",
      "medication_time": "2024-05-19",
      "source": "医院药品处方同步"
    },
    {
      "drug_name": "吡格列酮二甲双胍片",
      "specification": "30片",
      "usage": "口服",
      "frequency": "2/日(8am-4pm)",
      "single_dose": "500.0mg",
      "medication_time": "2024-05-19",
      "source": "医院药品处方同步"
    }
  ],
  "active_control_goals": [
    {
      "metric_name": "空腹血糖",
      "lower_bound": {
        "value": 4.4,
        "inclusive": false
      },
      "upper_bound": {
        "value": 7,
        "inclusive": false
      }
    },
    {
      "metric_name": "餐后血糖",
      "lower_bound": {
        "value": 4.4,
        "inclusive": false
      },
      "upper_bound": {
        "value": 10,
        "inclusive": false
      }
    }
  ]
}
```

## 关键说明

- `plan_type` 是总入口路由字段。`diet` 进入饮食方案工程，`sport` 进入运动方案工程；如果后续新增睡眠、用药、监测等专题，也应继续扩展该字段。
- 所有字段值建议直接传中文，便于模型生成中文干预方案。
- 时间字段建议统一使用 `YYYY-MM-DD HH:mm:ss`；仅日期字段可使用 `YYYY-MM-DD`。
- 最近一年数据建议只传已完成、已确认的数据，避免草稿或未完成记录干扰模型判断。
- `metric_records_last_1y` 使用统一指标记录结构，不按指标单独拆顶层字段。
- 血压可先使用字符串格式，例如 `"150/100"`；如果后续接口支持，也可以拆成收缩压和舒张压两个数值字段。
- 控制目标中 `inclusive=false` 表示不包含边界，例如截图中的 `> 4.4`、`< 7`。
- 未采集或无数据字段建议传 `null`、空字符串或空数组，保持字段结构稳定。

## 与字段清单的对应关系

字段路径以 JSON 路径为准。例如：

| JSON 字段路径 | 中文含义 |
| --- | --- |
| `plan_type` | 方案类型，`diet` 或 `sport` |
| `plan_goal_and_requirements` | 方案目标和额外要求 |
| `extra_supplement` | 额外补充信息 |
| `basic_profile.demographics.gender` | 性别 |
| `basic_profile.demographics.age` | 年龄 |
| `basic_profile.health_info.current_diseases[].name` | 现有疾病名称 |
| `disease_profile.diabetes_profile.diabetes_type` | 糖尿病类型 |
| `disease_profile.obesity_profile.body_signs.waist_cm` | 腰围 |
| `followup_records_last_1y[].lifestyle_status.staple_food_g_per_day` | 随访中的主食摄入量 |
| `metric_records_last_1y[].metric_name` | 指标名称 |
| `diet_records_last_1y[].calories_kcal` | 摄入热量 |
| `exercise_records_last_1y[].duration_minutes` | 运动时长 |
| `medication_pickup_records_last_1y[].drug_name` | 药品名称 |
| `active_control_goals[].lower_bound.inclusive` | 目标下限是否包含边界 |
