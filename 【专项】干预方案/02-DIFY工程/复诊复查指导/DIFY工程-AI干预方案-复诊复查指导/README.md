# DIFY工程-AI干预方案-复诊复查指导

## 工程定位

本工程用于在 DIFY 中搭建“AI 干预方案-复诊复查指导”分支。工作流接收患者基础档案、专病档案、近 1 年随访/指标/饮食/运动/取药记录、当前控制目标和健管师本次方案要求，输出可供 H5 渲染、健管师审阅修改的标准化复诊复查指导 JSON，并在等待期间输出用户可见的流式阶段分析。

本工程对应总入参 `planType=followup_review`。

本目录同时包含结构化 JSON 生成节点和 Chatflow 流式展示节点。测试数据只保留一套，统一放在 `测试数据/`。

## 节点总览

```mermaid
flowchart TB
  A["Start"] --> B["节点1：入参拆包与基础清洗"]

  B --> S1["流式节点A：健康状态与复诊需求识别"]
  S1 --> AS1["Answer A：健康状态与复诊需求识别"]
  AS1 --> S2["流式节点B：复查项目与时间窗口校准"]
  S2 --> AS2["Answer B：复查项目与时间窗口校准"]
  AS2 --> S3["流式节点C：复诊准备与异常触发指导"]
  S3 --> AS3["Answer C：复诊准备与异常触发指导"]

  AS1 --> C["节点2：生成并保护复诊复查素材摘要"]
  C --> D["节点3：规划分组并生成复诊复查指导 items"]
  C --> E["节点4：生成顶层总述字段"]

  D --> F["节点5：组装最终 JSON + 校验兜底"]
  E --> F
  F --> G["End/Answer：输出 finalPlanJsonText"]
```

说明：流式节点只输出自然语言过程展示，不参与最终 JSON 拼装；结构化节点仍负责生成、格式化和组装最终 `finalPlanJsonText`。

## Start 入参建议

```json
{
  "planType": "followup_review",
  "planGoalAndRequirements": "",
  "extraSupplement": "",
  "basicProfile": {},
  "diseaseProfile": {},
  "followupRecordsLast1y": [],
  "metricRecordsLast1y": [],
  "dietRecordsLast1y": [],
  "exerciseRecordsLast1y": [],
  "medPickupRecords1y": [],
  "activeControlGoals": []
}
```

## 最终输出

节点5输出：

```json
{
  "finalPlanJson": {
    "planName": "复诊复查指导",
    "planTitle": "个性化复诊复查安排",
    "planSummary": "方案概述",
    "executionPoints": "执行要点",
    "groups": []
  },
  "finalPlanJsonText": "{}",
  "validationErrors": [],
  "validationErrorsCount": 0,
  "groupsCount": 0
}
```

建议最终 Answer 节点统一返回 `finalPlanJsonText`。如果 Dify 内部节点同时保留 `finalPlanJson` Object，下游 H5 仍以 `finalPlanJsonText` 为准。

## 编排要点

- 节点1会带出 `planType`，如果不是 `followup_review` 会在 `routeWarning` 中提示调用方检查路由。
- 节点2用 1 个 LLM 同时生成 `medicalStatusSummary`、`reviewNeedSummary`、`safetyTriggerSummary`，再用代码保护出参格式，输出稳定的 `materialSummaryBundle`。
- 节点2只做“证据摘要”，不直接生成患者最终建议正文。
- 节点3用 1 个 LLM 同时输出 `groupPlan` 和 `groups/items`，再用代码保护出参格式。
- 节点3生成 `groups/items` 时要求 `importance` 只能取 `重点执行`、`常规建议`、`补充建议`，且 group/item 同层字段必须齐全。
- 节点4与节点3并行生成顶层文案字段，不依赖 `groups/items`，并用代码保护出参格式。
- 节点5负责组装节点3和节点4的出参，并做排序、字段兜底和结构校验。
- 面向用户的流式输出不暴露结构化 JSON、schema、代码节点日志和提示词工程细节。

## 流式输出设计

| 流式节点 | 触发时机 | 展示重点 |
| --- | --- | --- |
| 流式节点A：健康状态与复诊需求识别 | 入参清洗后 | 正在分析基础健康信息、慢病背景、近期指标、随访记录和既往治疗连续性 |
| 流式节点B：复查项目与时间窗口校准 | 健康状态识别后 | 校准需要关注的复查项目、优先级和建议时间窗口 |
| 流式节点C：复诊准备与异常触发指导 | 复查项目校准后 | 说明复诊前资料准备、结果回传方式，以及哪些异常需要提前就医 |

流式输出建议控制在 80-140 字的自然段，像健管师解释“正在看什么、正在判断什么、接下来如何安排复诊复查”，不提前展开完整建议清单。

## 文件结构

联调 demo 位于 `../../demo/`，用于统一测试整个干预方案 V3 Chatflow。

```text
DIFY工程-AI干预方案-复诊复查指导/
  README.md
  节点1-入参拆包与基础清洗/
  节点2-素材摘要/
  节点3-规划分组并生成复诊复查指导items/
  节点4-生成顶层总述字段/
  节点5-组装最终JSON+校验兜底/
  流式节点A-健康状态与复诊需求识别/
  流式节点B-复查项目与时间窗口校准/
  流式节点C-复诊准备与异常触发指导/
  测试数据/
```
