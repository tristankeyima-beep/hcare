# 2026-05-15 运动方案 Chatflow 真实 DIFY 调试记录

## 调试目标

验证“AI干预方案-运动方案-得到JSON”在 DIFY 中使用 `planType=sport` 时，能否通过 Chatflow API 正常生成运动方案最终 JSON。

## 调试环境

- DIFY API Base: `https://dify.hzmarvel.com/v1`
- 接口: `/chat-messages`
- 调用模式: `response_mode=streaming`
- API Key: 已脱敏，调试时使用用户提供的 `app-***`
- demo 脚本:
  `/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-饮食方案-得到JSON/demo/dify-chatflow-streaming-demo.mjs`
- 运动方案测试入参:
  `/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-运动方案-得到JSON/测试数据/【入参】运动方案工作流测试入参.json`

## 复跑命令

```bash
DIFY_API_KEY='app-***' \
DIFY_PLAN_TYPE='sport' \
DIFY_QUERY='请根据基础档案生成运动方案。' \
node '/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-饮食方案-得到JSON/demo/dify-chatflow-streaming-demo.mjs' \
'/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-运动方案-得到JSON/测试数据/【入参】运动方案工作流测试入参.json'
```

## 调试过程

### 1. 初次运行：代码节点默认值配置错误

接口连接成功，返回 `200 text/event-stream`，但流中直接返回 error，没有进入业务节点。

错误信息：

```text
invalid_param
CodeNodeData default_value.4
Invalid JSON format for value: {"组装最终JSON失败了"}
key: finalPlanJson
```

判断：DIFY 中“节点5-组装最终JSON+校验兜底”的 `finalPlanJson` 默认值不是合法 JSON 对象。

修正建议：

```json
{}
```

或：

```json
{"error":"组装最终JSON失败了"}
```

### 2. 第二次运行：节点1输出字段名不一致

工作流已能进入 `sport` 分支，但“患者档案数据整理”失败。

错误信息：

```text
Run failed: Output safetyEnergyContext is missing.
```

本地代码实际返回字段：

```text
safetyBoundaryContext
```

判断：DIFY 页面中“患者档案数据整理”代码节点输出变量配置为 `safetyEnergyContext`，与本地代码和说明文档不一致。

修正：将 DIFY 输出变量改为 `safetyBoundaryContext`。

### 3. 第三次运行：两个结构化保护节点异常

工作流能跑到最终 answer，但状态为 `partial-succeeded`，最终输出为兜底 JSON。

失败节点：

```text
将运动方案分组清单结构化: Output groupPlan is missing.
将运动方案总述结构化: Not all output parameters are validated.
```

进一步抓取节点输入输出后确认：

- DIFY 实际传给两个保护代码节点的字段名是 `llmText`
- 本地代码只读取 `llmOutput`
- 因此节点3无法读取 LLM 原文，输出 `groupPlanCount=0`、`groupsCount=0`
- 节点4拿到合法 JSON，但代码没有读取到该字段，导致全部兜底或校验失败

### 4. 本地代码修正

更新以下两个代码文件，使其兼容 `llmOutput` 和 DIFY 实际传入的 `llmText`：

- `节点3-规划分组并生成运动方案items/代码-保护分组与itemsLLM出参.py`
- `节点4-生成顶层总述字段/代码-保护顶层总述LLM出参.py`

核心改动：

```python
def _pick_llm_output(llmOutput=None, llmText=None):
    if llmOutput not in (None, ""):
        return llmOutput
    return llmText
```

节点3：

```python
def main(llmOutput=None, llmText=None, groupPlan=None, groups=None, **kwargs) -> dict:
    parsed = _parse_json(_pick_llm_output(llmOutput, llmText), {})
```

节点4：

```python
def main(
    llmOutput=None,
    llmText=None,
    planName: str = "",
    planTitle: str = "",
    planSummary: str = "",
    executionPoints: str = "",
    **kwargs
) -> dict:
    parsed = _parse_json(_pick_llm_output(llmOutput, llmText), {})
```

同步更新同级说明文档：

- `节点3-规划分组并生成运动方案items/【代码出入参说明】代码-保护分组与itemsLLM出参.md`
- `节点4-生成顶层总述字段/【代码出入参说明】代码-保护顶层总述LLM出参.md`

新增说明：`llmText` 为 DIFY 节点实际传入字段；当 `llmOutput` 为空时读取 `llmText`。

### 5. 本地验证

使用本地 Python 直接调用两个节点函数，验证 `llmText` 可被正确读取。

结果：

```text
node3 groupPlanCount: 1
node3 groupsCount: 1
node4 planTitle: 测试标题
node4 fallbackFieldsCount: 0
```

### 6. 最终复跑结果

更新 DIFY 节点代码后再次使用同一份入参复跑，工作流全部节点成功。

节点状态：

```text
用户输入: succeeded
条件分支: succeeded
患者档案数据整理: succeeded
运动方案素材摘要整理: succeeded
将LLM生成的运动画像结构化: succeeded
方案内容分组并生成运动方案: succeeded
生成运动干预方案总述: succeeded
将运动方案分组清单结构化: succeeded
将运动方案总述结构化: succeeded
组装最终JSON: succeeded
输出最终结构化运动干预方案: succeeded
```

运行摘要：

```json
{
  "answerChars": 7168,
  "totalTokens": 9785,
  "totalPrice": "0.015002",
  "currency": "RMB"
}
```

最终方案标题：

```text
控糖减重运动管理方案
```

## 最终结论

`planType=sport` 的运动方案 Chatflow 已经跑通。最终成功运行时所有节点均为 `succeeded`，不再出现 `partial-succeeded`、`exception` 或兜底 JSON。

本次问题主要来自 DIFY 页面节点配置与本地代码字段口径不一致：

- `finalPlanJson` 默认值不是合法 JSON
- `safetyEnergyContext` 与本地返回字段 `safetyBoundaryContext` 不一致
- DIFY 实际传参为 `llmText`，本地保护代码原先只读取 `llmOutput`

