# 饮食方案 C 端 H5 字段对应说明

对应页面：`patient-diet-plan-c-end.html`

数据来源：饮食方案最终出参 JSON。当前 HTML 为了方便直接预览，把同结构数据内嵌在 `script#plan-data` 中；前端接接口时可替换为接口返回对象。

## 结论

页面里的“方案内容”来自出参 JSON 字段，或由出参 JSON 做简单计算得到。页面仍保留少量固定 UI 文案，用于按钮、单位、模块提示，不属于方案业务内容。

## 顶层数据

| 页面位置 | 展示内容 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 浏览器标题 | 饮食健康处方 | `plan_name` | 当前 HTML 的 `<title>` 写死为示例标题；前端可用 `plan_name` 设置页面标题 |
| 内嵌数据源 | 完整方案数据 | 根对象 | 当前从 `script#plan-data` 读取；接口接入时替换为接口出参 |
| 未展示字段 | 方案摘要 | `plan_summary` | 当前封面版未展示，可作为分享摘要或详情说明备用 |

## 封面区

| 页面位置 | 展示内容示例 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 封面右上角 | 饮食健康处方 | `plan_name` | 直接展示 |
| 封面主标题 | 个性化控糖减重饮食建议 | `plan_title` | 直接展示 |
| 患者专属标签 | 张三专属方案 | 外部患者信息接口：`patient_name` | 不来自饮食方案出参；姓名后拼固定文案“专属方案” |
| 封面副标题 | 最近7天饮食执行菜谱 | `groups[].group_title` | 取 `group_type === "weekly_meal_plan"` 的分组 |
| 封面目标 | 目标：减重控糖 | `groups[].diet_plan_goal_label` | 取 `weekly_meal_plan` 分组，前面拼固定标签“目标：” |
| 统计 1 | 7 天 / 三餐安排 | `groups[].items.length` | 取 `weekly_meal_plan.items.length` |
| 统计 2 | 1584 / 日均千卡 | `groups[].items[].daily_total_kcal` | 对 7 天 `daily_total_kcal` 求平均并四舍五入 |
| 统计 3 | 404 / 日均缺口 | `groups[].items[].estimated_energy_deficit_kcal` | 对 7 天 `estimated_energy_deficit_kcal` 求平均并四舍五入 |

固定 UI 文案：`三餐安排`、`日均千卡`、`日均缺口`、`向下查看今天先吃什么`。

## 今日执行卡

| 页面位置 | 展示内容示例 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 卡片标题 | 今天先按第1天执行 | `weekly_meal_plan.items[0].title` | 拼接固定前缀“今天先按”和后缀“执行” |
| 标签 | 减重控糖 | `weekly_meal_plan.diet_plan_goal_label` | 直接展示 |
| 今日说明 | 三餐以燕麦、糙米饭... | `weekly_meal_plan.items[0].content` | 直接展示 |
| 指标：千卡 | 1560 | `weekly_meal_plan.items[0].daily_total_kcal` | 直接展示 |
| 指标：蛋白质 | 88g | `weekly_meal_plan.items[0].daily_total_protein_g` | 数值后拼 `g` |
| 指标：脂肪 | 45g | `weekly_meal_plan.items[0].daily_total_fat_g` | 数值后拼 `g` |
| 指标：热量缺口 | 420 | `weekly_meal_plan.items[0].estimated_energy_deficit_kcal` | 直接展示 |
| 关注点 | 晚餐主食偏轻... | `weekly_meal_plan.items[0].focus_point` | 直接展示 |

固定 UI 文案：`千卡`、`蛋白质`、`脂肪`、`热量缺口`。

## 执行要点

| 页面位置 | 展示内容 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 模块标题 | 执行要点 | 固定 UI 文案 | 不来自 JSON |
| 右侧提示 | 先按这几条做 | 固定 UI 文案 | 不来自 JSON |
| 正文 | 优先执行最近7天菜谱... | `execution_points` | 直接展示 |

## 普通饮食建议

| 页面位置 | 展示内容示例 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 模块标题 | 主食与血糖管理 / 外食与夜班饮食策略 | `groups[].group_title` | 取所有 `group_type === "advice_list"` 的分组标题，用 `/` 拼接 |
| 条数 | 2 条重点 | `advice_list.items.length` | 展平所有 advice_list 分组的 items 后计数 |
| 建议标题 | 固定主食份量 | `advice_list.items[].title` | 直接展示 |
| 标签 | 重点执行 | `advice_list.items[].importance` | 直接展示 |
| 建议正文 | 每餐主食先控制... | `advice_list.items[].content` | 直接展示 |
| 关注点 | 重点降低餐后血糖波动... | `advice_list.items[].focus_point` | 直接展示 |

当前未展示但可备用字段：`groups[].group_summary`、`groups[].display_style`、`items[].item_type`。

## 最近 7 天菜谱

| 页面位置 | 展示内容示例 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 模块标题 | 最近7天饮食执行菜谱 | `weekly_meal_plan.group_title` | 直接展示 |
| 右侧摘要 | 日均 1584 千卡 | `weekly_meal_plan.items[].daily_total_kcal` | 求平均并四舍五入 |
| 日期按钮主文案 | 第 1 天 | `weekly_meal_plan.items[].day` | 拼接“第 X 天” |
| 日期按钮副文案 | 1560 千卡 | `weekly_meal_plan.items[].daily_total_kcal` | 数值后拼 `千卡` |
| 当天标题 | 第1天三餐安排 | `weekly_meal_plan.items[].title` | 拼接后缀“三餐安排” |
| 当天标签 | 重点执行 | `weekly_meal_plan.items[].importance` | 直接展示 |
| 当天说明 | 三餐以燕麦... | `weekly_meal_plan.items[].content` | 直接展示 |
| 当天指标 | 千卡、蛋白质、脂肪、热量缺口 | `daily_total_kcal`、`daily_total_protein_g`、`daily_total_fat_g`、`estimated_energy_deficit_kcal` | 直接展示或拼单位 |
| 当天关注点 | 晚餐主食偏轻... | `weekly_meal_plan.items[].focus_point` | 直接展示 |

当前未展示但可备用字段：`weekly_meal_plan.group_summary`、`weekly_meal_plan.goal_basis`、`weekly_meal_plan.diet_plan_goal`、`weekly_meal_plan.display_style`。

## 三餐与食物明细

| 页面位置 | 展示内容示例 | 字段来源 | 处理方式 |
| --- | --- | --- | --- |
| 餐次名称 | 早餐 | `weekly_meal_plan.items[].meals[].meal_name` | 直接展示 |
| 餐次热量 | 390 千卡 | `meals[].meal_total_kcal` | 数值后拼 `千卡` |
| 食物名称 | 燕麦 | `meals[].foods[].name` | 直接展示 |
| 食物克重 | 40g | `foods[].amount_g` | 数值后拼 `g` |
| 食物热量 | 150千卡 | `foods[].kcal` | 数值后拼 `千卡` |

当前未展示但可备用字段：`meals[].meal_total_protein_g`、`meals[].meal_total_fat_g`、`foods[].protein_g`、`foods[].fat_g`。

## 固定 UI 文案清单

这些文案是页面结构和操作提示，不属于方案业务内容字段：

| 页面位置 | 固定文案 |
| --- | --- |
| 封面统计单位 | 三餐安排、日均千卡、日均缺口 |
| 封面引导 | 向下查看今天先吃什么 |
| 执行要点标题 | 执行要点 |
| 执行要点提示 | 先按这几条做 |
| 今日卡标题拼接 | 今天先按、执行 |
| 菜谱日标题拼接 | 第、天、三餐安排 |
| 单位 | g、千卡 |
| 底部按钮 | 问健管师、查看今日三餐 |

## 前端筛字段建议

外部患者信息接口需要额外提供：

```text
patient_name
```

最小必需字段：

```text
plan_name
plan_title
execution_points
groups[].group_title
groups[].group_type
groups[].items[]
```

当 `group_type === "advice_list"` 时，前端至少需要：

```text
items[].title
items[].content
items[].focus_point
items[].importance
```

当 `group_type === "weekly_meal_plan"` 时，前端至少需要：

```text
diet_plan_goal_label
items[].day
items[].title
items[].content
items[].daily_total_kcal
items[].daily_total_protein_g
items[].daily_total_fat_g
items[].estimated_energy_deficit_kcal
items[].focus_point
items[].importance
items[].meals[].meal_name
items[].meals[].meal_total_kcal
items[].meals[].foods[].name
items[].meals[].foods[].amount_g
items[].meals[].foods[].kcal
```
