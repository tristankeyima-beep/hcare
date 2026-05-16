# DIFY工程-AI干预方案-V3-chatflow

## 工程定位

这是当前 AIHcare 干预方案的统一 Dify Chatflow 工程，Dify 应用名为 `干预方案-V3-chatflow`，应用模式为 `advanced-chat`。

这份 Chatflow 同时承载饮食方案和运动方案，不再按“饮食 workflow / 饮食 chatflow / 运动 workflow / 运动 chatflow”拆成 4 个独立 Dify 应用。实际运行时通过入参 `planType` 分流：

- `planType` 包含 `diet`：进入饮食干预方案分支。
- `planType` 包含 `sport`：进入运动干预方案分支。

## 调试工具中的 4 个入口

`99-DIFY工作流运行测试/workflow-registry.json` 里仍保留 4 个 `workflow-key`，是为了测试和阅读时更方便定位目标，但它们都指向同一个 V3 Chatflow：

| workflow-key | 含义 | 分支 | 测试视角 |
| --- | --- | --- | --- |
| `aihcare-diet-workflow` | 饮食方案结构化结果测试 | `planType=diet` | 关注最终 `finalPlanJsonText` |
| `aihcare-diet-chatflow` | 饮食方案流式过程测试 | `planType=diet` | 关注流式阶段输出和最终 `finalPlanJsonText` |
| `aihcare-sport-workflow` | 运动方案结构化结果测试 | `planType=sport` | 关注最终 `finalPlanJsonText` |
| `aihcare-sport-chatflow` | 运动方案流式过程测试 | `planType=sport` | 关注流式阶段输出和最终 `finalPlanJsonText` |

## Dify 导出文件

- 导出文件：`干预方案-V3-chatflow.yml`
- Dify 应用名：`干预方案-V3-chatflow`
- Dify 应用模式：`advanced-chat`
- Dify 导出版本：`0.5.0`

## 主要入参

Chatflow 起始入参包含：

- `planType`：方案类型，当前用于区分 `diet` / `sport`。
- `planGoalAndRequirements`：方案目标与要求。
- `extraSupplement`：额外补充信息。
- `basicProfile`：基础档案。
- `diseaseProfile`：疾病档案。
- `followupRecordsLast1y`：近一年随访记录。
- `metricRecordsLast1y`：近一年指标记录。
- `dietRecordsLast1y`：近一年饮食记录。
- `exerciseRecordsLast1y`：近一年运动记录。
- `medPickupRecords1y`：近一年取药记录。
- `activeControlGoals`：主动控制目标。

## 分支产出

### 饮食分支

饮食分支会依次完成健康画像与慢病风险识别、管理目标与安全边界校准、饮食画像结构化、饮食建议行动化推导、七天餐单执行策略生成、菜谱结构化、总述结构化和最终 JSON 组装。

最终 Answer 节点为：`输出最终结构化饮食干预方案`。

最终结果包裹在：

```xml
<FINAL_PLAN_JSON>...</FINAL_PLAN_JSON>
```

### 运动分支

运动分支会依次完成运动画像与风险识别、运动目标与安全边界校准、素材摘要整理、运动建议行动化生成、运动方案分组清单结构化、总述结构化和最终 JSON 组装。

最终 Answer 节点为：`输出最终结构化运动干预方案`。

最终结果包裹在：

```xml
<FINAL_PLAN_JSON>...</FINAL_PLAN_JSON>
```

## 文件结构

```text
DIFY工程-AI干预方案-V3-chatflow/
  README.md
  干预方案-V3-chatflow.yml
```

## 历史拆分工程

以下目录仍保留，用作分支设计说明、节点说明、测试入参和历史调试记录参考；当前主线以本 V3 Chatflow 为准。

这些目录不是 4 个独立 Dify 应用，而是同一个 `干预方案-V3-chatflow` 的资料拆分方式。

- `DIFY工程-AI干预方案-饮食方案-得到JSON/`
- `DIFY工程-AI干预方案-饮食方案-Chatflow流式版/`
- `DIFY工程-AI干预方案-运动方案-得到JSON/`
- `DIFY工程-AI干预方案-运动方案-Chatflow流式版/`
