# 02-DIFY工程

这个目录记录 AIHcare 干预方案相关的 Dify 工程、节点说明、测试数据和历史调试记录。

## 当前主线工程

当前主线是统一版 Chatflow：

- `DIFY工程-AI干预方案-V3-chatflow/`
- Dify 应用名：`干预方案-V3-chatflow`
- Dify 应用模式：`advanced-chat`
- 导出文件：`DIFY工程-AI干预方案-V3-chatflow/干预方案-V3-chatflow.yml`

这份 V3 Chatflow 同时承载饮食方案和运动方案，通过入参 `planType` 分支：

- `planType=diet`：饮食干预方案。
- `planType=sport`：运动干预方案。

调试工具里的 `aihcare-diet-workflow`、`aihcare-diet-chatflow`、`aihcare-sport-workflow`、`aihcare-sport-chatflow` 不是 4 个独立 Dify 应用，而是同一个 V3 Chatflow 的 4 个测试入口或阅读视角。

## 4 个资料目录和统一 Chatflow 的关系

下面 4 个目录是为了把饮食 / 运动、最终 JSON / 流式过程的资料分开管理，方便查 Prompt、代码节点、测试入参和历史调试记录。它们不是 4 个 Dify 应用。

| 目录 | 对应 V3 分支 | 资料用途 |
| --- | --- | --- |
| `DIFY工程-AI干预方案-饮食方案-得到JSON/` | `planType=diet` | 饮食分支最终 `finalPlanJsonText` 的节点设计、测试数据和历史调试记录 |
| `DIFY工程-AI干预方案-饮食方案-Chatflow流式版/` | `planType=diet` | 饮食分支流式阶段输出的节点设计和测试数据 |
| `DIFY工程-AI干预方案-运动方案-得到JSON/` | `planType=sport` | 运动分支最终 `finalPlanJsonText` 的节点设计、测试数据和历史调试记录 |
| `DIFY工程-AI干预方案-运动方案-Chatflow流式版/` | `planType=sport` | 运动分支流式阶段输出的节点设计和测试数据 |

实际导入 Dify 和调用接口时，以 `DIFY工程-AI干预方案-V3-chatflow/干预方案-V3-chatflow.yml` 为当前主线文件。

## 文件结构

```text
02-DIFY工程/
  README.md
  饮食方案工作流设计总览.md
  DIFY工程-AI干预方案-V3-chatflow/
    README.md
    干预方案-V3-chatflow.yml
  DIFY工程-AI干预方案-饮食方案-得到JSON/
    README.md
    demo/
    测试数据/
    真实DIFY调试/
    节点1-入参拆包与基础清洗/
    节点2-患者饮食管理画像/
    节点3-生成普通饮食建议groups/
    节点4-生成7天菜谱group/
    节点5-生成顶层总述字段/
    节点6-组装最终JSON+校验兜底/
  DIFY工程-AI干预方案-饮食方案-Chatflow流式版/
    README.md
    测试数据/
    流式节点A-健康画像与慢病风险识别/
    流式节点B-管理目标与安全边界校准/
    流式节点C-饮食建议行动化推导/
    流式节点D-七天餐单执行策略生成/
  DIFY工程-AI干预方案-运动方案-得到JSON/
    README.md
    测试数据/
    真实dify调试记录/
    节点1-入参拆包与基础清洗/
    节点2-素材摘要/
    节点3-规划分组并生成运动方案items/
    节点4-生成顶层总述字段/
    节点5-组装最终JSON+校验兜底/
  DIFY工程-AI干预方案-运动方案-Chatflow流式版/
    README.md
    测试数据/
    流式节点A-运动画像与风险识别/
    流式节点B-运动目标与安全边界校准/
    流式节点C-运动建议行动化生成/
```

## 分支资料说明

4 个分支资料目录仍然有价值，主要用于：

- 查找旧版节点设计、Prompt、代码节点和出入参说明。
- 查找饮食或运动分支的默认测试入参。
- 回看真实 Dify 调试记录。
- 对照 V3 Chatflow 中饮食和运动两条分支的实现目标。

后续新增 Dify 导出文件时，优先放入独立工程目录，并在本 README 和 `99-DIFY工作流运行测试/workflow-registry.json` 中同步登记。
