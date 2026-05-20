# AIHcare 运动方案 Dify Chatflow 运行测试

这个目录用于本地测试 AIHcare 运动干预方案 Chatflow，并按病例归档每次 Dify 调用的原始事件、最终 JSON 和 HTML 质控报告。

## API Key

不要把真实 Key 写入仓库文件。运行时通过环境变量传入：

```bash
export DIFY_API_KEY_TEST="app-***"
```

也可以使用通用 `DIFY_API_KEY`，或在单次运行时使用 `--api-key` 覆盖。Key 读取优先级：

1. `--api-key`
2. `DIFY_API_KEY_<环境名大写>`，例如 `DIFY_API_KEY_TEST`、`DIFY_API_KEY_PROD`
3. `DIFY_API_KEY`

归档结果和 HTML 中的请求头只显示 `Bearer ***`。

## 使用流程

### 1. 生成 case 入参

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-运动方案-得到JSON/demo"
python3 dify_aihcare_sport_runner.py prepare-input --env-name test --input "../测试数据/【入参】运动方案工作流测试入参.json"
```

生成：

```text
userinput/<患者名称>_运动方案_<记录时间>/入参.json
```

`prepare-input` 会兼容两种入参形态：

- 原始 JSON 顶层就是 Dify inputs 字段。
- 原始 JSON 顶层包含 `inputs` 对象。

处理规则：

- 对象和数组会转为 JSON 字符串，以适配 Dify paragraph 变量。
- 自动补齐 `planType=sport`。
- 移除 `response_mode`、`user`、`conversation_id`、`query` 等请求控制字段。
- 患者名称提取顺序：`externalPatientInfo.patientName`、顶层 `patientName/patient_name/姓名`、`basicProfile.demographics.name`、`未知患者`。

### 2. 调用 Dify Chatflow

复制 `prepare-input` 输出的普通终端命令，或手动执行：

```bash
DIFY_API_KEY_TEST="app-***" python3 dify_aihcare_sport_runner.py run --env-name test --case-dir "userinput/未知患者_运动方案_20260519-101112"
```

默认调用：

- `POST https://dify.hzmarvel.com/v1/chat-messages`
- `response_mode: "streaming"`
- `query: "请根据基础档案生成运动方案。"`
- `user: "dify-aihcare-sport-chatflow-test"`
- `transport: "curl"`

可选参数：

- `--env-name test`：指定环境名，进入结果目录、文件名、raw-result 和 HTML 报告。
- `--query "请根据基础档案生成运动方案。"`：覆盖默认 query。
- `--api-base https://dify.hzmarvel.com/v1`：覆盖 Dify API 地址。
- `--api-key app-***`：覆盖环境变量。
- `--transport urllib`：不用 curl，改走 Python urllib 调试。

### 3. 查看归档结果

每次调用会写入同一个 case 目录下的独立子目录：

```text
userinput/<患者名称>_运动方案_<记录时间>/<调用时间>_<环境名>_<messageid-or-no-messageid>/
```

子目录内固定生成：

- `<调用时间>_<环境名>_<id>_raw-result.json`
- `<调用时间>_<环境名>_<id>_events.ndjson`
- `<调用时间>_<环境名>_<id>_result.html`

HTML 质控报告包含：

- 运行概览。
- 输入充分性和有效信息展开表格。
- 运动方案分组、建议条目、重点执行条目和安全提醒覆盖情况。
- 节点耗时、慢节点和失败节点。
- 默认收起的完整原始数据。

### 4. 重新渲染 HTML

```bash
python3 dify_aihcare_sport_runner.py render-html --record "userinput/未知患者_运动方案_20260519-101112/20260519-102000_msg-1/20260519-102000_msg-1_raw-result.json"
```

## 本地测试

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-运动方案-得到JSON"
python3 -m unittest discover demo/tests
python3 -m py_compile demo/dify_aihcare_sport_runner.py demo/tests/test_dify_aihcare_sport_runner.py
```
