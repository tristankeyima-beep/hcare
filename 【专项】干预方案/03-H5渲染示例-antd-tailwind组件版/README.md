# 干预方案展示组件 - antd + Tailwind

这是从 `03-H5渲染示例` 复制出的 antd + Tailwind 组件版示例。

## 内容来源

- `data/diet-final-plan.json`：参考原饮食方案 `dify-final-plan.json`
- `data/exercise-final-plan.json`：参考原运动方案 `dify-final-plan.json`

## 页面说明

- `index.html` 是入口导航。
- `diet.html` 使用 React + antd + Tailwind，独立加载饮食方案。
- `exercise.html` 使用 React + antd + Tailwind，独立加载运动方案。
- `vendor/` 保存本地预览所需的浏览器脚本，包含 React、dayjs、antd、Babel 和 Tailwind，避免本地验证时受 CDN 网络影响。
- 核心组件名为 `InterventionPlanShowcase`。
- 展示逻辑继续以方案 JSON 的 `groups` 为主：
  - `adviceList` 渲染为建议卡片。
  - `weeklyMealPlan` 仅在饮食方案中渲染为 7 日菜谱。
  - `executionPoints` 渲染为执行要点。
- 患者名 `张三专属方案` 仅作为封面展示信息，不写入业务 JSON。

## 字段来源核对

业务展示字段均来自当前页面加载的 final JSON：

- 顶部方案信息：`planName`、`planTitle`、`planSummary`
- 建议分组：`groups[].groupTitle`、`groups[].groupSummary`、`groups[].items[]`
- 建议内容：`title`、`content`、`importance`、`focusPoint`
- 饮食 7 日菜谱：`weeklyMealPlan` 分组下的 `items[]`、`meals[]`、`foods[]`
- 饮食营养数据：`dailyTotalKcal`、`dailyTotalProteinG`、`dailyTotalFatG`、`dailyTotalCarbsG`、`estimatedEnergyDeficitKcal`
- 执行要点：`executionPoints`

运动方案不会展示 final JSON 中不存在的菜谱、餐次、食物或日均能量字段。

非 JSON 的内容仅保留为组件 UI 文案或展示层入参，例如患者姓名 `张三`、Tab 标题、表格列名、单位和空状态。

## 本地预览

在当前目录启动静态服务后访问 `index.html`。页面需要通过 HTTP 访问，直接双击打开时浏览器可能会阻止 JSON 加载。
