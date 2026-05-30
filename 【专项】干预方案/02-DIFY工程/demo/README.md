# AIHcare 干预方案 Dify Chatflow 运行测试

这个目录用于本地测试 AIHcare 干预方案 V3 Chatflow。它是整个干预方案的联调 demo，不归属于单独的饮食或运动分支。

当前包含：

- `dify_aihcare_diet_runner.py`：饮食方案 `planType=diet` 调用、归档和 HTML 渲染。
- `dify_aihcare_sport_runner.py`：运动方案 `planType=sport` 调用、归档和 HTML 渲染。
- `dify_aihcare_followup_review_runner.py`：复诊复查指导 `planType=followup_review` 调用、归档和 HTML 渲染。
- `dify_aihcare_health_weekly_report_runner.py`：健康周报 `planType=health_weekly_report` 调用、归档和 HTML 渲染。
- `tests/`：本地单测，覆盖 runner 和部分工作流 Code 节点。
- `userinput/`：按病例归档的入参、Dify 原始事件、最终 JSON 和 HTML 结果页。

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

## 饮食方案

### 1. 生成 case 入参

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/demo"
python3 dify_aihcare_diet_runner.py prepare-input --env-name test
```

默认读取：

```text
../饮食方案/DIFY工程-AI干预方案-饮食方案/测试数据/【入参】饮食方案工作流测试入参.json
```

也可以显式指定输入：

```bash
python3 dify_aihcare_diet_runner.py prepare-input \
  --env-name test \
  --input "../饮食方案/DIFY工程-AI干预方案-饮食方案/测试数据/【入参】饮食方案工作流测试入参.json"
```

### 2. 调用 Dify Chatflow

复制 `prepare-input` 输出的普通终端命令，或手动执行：

```bash
DIFY_API_KEY_TEST="app-***" python3 dify_aihcare_diet_runner.py run --env-name test --case-dir "userinput/未知患者_饮食方案_20260519-101112"
```

默认调用：

- `POST https://dify.hzmarvel.com/v1/chat-messages`
- `response_mode: "streaming"`
- `query: "生成干预方案"`
- `user: "dify-aihcare-diet-chatflow-test"`
- `transport: "curl"`

## 运动方案

### 1. 生成 case 入参

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/demo"
python3 dify_aihcare_sport_runner.py prepare-input --env-name test
```

默认读取：

```text
../运动方案/DIFY工程-AI干预方案-运动方案/测试数据/【入参】运动方案工作流测试入参.json
```

也可以显式指定输入：

```bash
python3 dify_aihcare_sport_runner.py prepare-input \
  --env-name test \
  --input "../运动方案/DIFY工程-AI干预方案-运动方案/测试数据/【入参】运动方案工作流测试入参.json"
```

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

## 复诊复查指导

### 1. 生成 case 入参

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/demo"
python3 dify_aihcare_followup_review_runner.py prepare-input --env-name test
```

默认读取：

```text
../复诊复查指导/DIFY工程-AI干预方案-复诊复查指导/测试数据/【入参】复诊复查指导工作流测试入参.json
```

也可以显式指定输入：

```bash
python3 dify_aihcare_followup_review_runner.py prepare-input \
  --env-name test \
  --input "../复诊复查指导/DIFY工程-AI干预方案-复诊复查指导/测试数据/【入参】复诊复查指导工作流测试入参.json"
```

### 2. 调用 Dify Chatflow

复制 `prepare-input` 输出的普通终端命令，或手动执行：

```bash
DIFY_API_KEY_TEST="app-***" python3 dify_aihcare_followup_review_runner.py run --env-name test --case-dir "userinput/未知患者_复诊复查指导_20260519-101112"
```

默认调用：

- `POST https://dify.hzmarvel.com/v1/chat-messages`
- `response_mode: "streaming"`
- `query: "请根据基础档案生成复诊复查指导。"`
- `user: "dify-aihcare-followup-review-chatflow-test"`
- `transport: "curl"`

## 健康周报

### 1. 生成 case 入参

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/demo"
python3 dify_aihcare_health_weekly_report_runner.py prepare-input --env-name test
```

默认读取：

```text
../健康周报/DIFY工程-AI干预方案-健康周报/测试数据/【入参】健康周报工作流测试入参.json
```

也可以显式指定输入：

```bash
python3 dify_aihcare_health_weekly_report_runner.py prepare-input \
  --env-name test \
  --input "../健康周报/DIFY工程-AI干预方案-健康周报/测试数据/【入参】健康周报工作流测试入参.json"
```

### 2. 调用 Dify Chatflow

复制 `prepare-input` 输出的普通终端命令，或手动执行：

```bash
DIFY_API_KEY_TEST="app-***" python3 dify_aihcare_health_weekly_report_runner.py run --env-name test --case-dir "userinput/未知患者_健康周报_20260519-101112"
```

默认调用：

- `POST https://dify.hzmarvel.com/v1/chat-messages`
- `response_mode: "streaming"`
- `query: "请根据基础档案生成健康周报。"`
- `user: "dify-aihcare-health-weekly-report-chatflow-test"`
- `transport: "curl"`

## 入参处理规则

`prepare-input` 会兼容两种入参形态：

- 原始 JSON 顶层就是 Dify `inputs` 字段。
- 原始 JSON 顶层包含 `inputs` 对象。

处理规则：

- 对象和数组会转为 JSON 字符串，以适配 Dify paragraph 变量。
- 饮食 runner 自动补齐 `planType=diet`，运动 runner 自动补齐 `planType=sport`，复诊复查指导 runner 自动补齐 `planType=followup_review`，健康周报 runner 自动补齐 `planType=health_weekly_report`。
- 移除 `response_mode`、`user`、`conversation_id`、`query` 等请求控制字段。
- 患者名称提取顺序：`externalPatientInfo.patientName`、顶层 `patientName/patient_name/姓名`、`basicProfile.demographics.name`、`未知患者`。

## 归档结果

每次调用会写入同一个 case 目录下的独立子目录：

```text
userinput/<患者名称>_<方案类型>_<记录时间>/<调用时间>_<环境名>_<messageid-or-no-messageid>/
```

子目录内固定生成：

- `<调用时间>_<环境名>_<id>_raw-result.json`
- `<调用时间>_<环境名>_<id>_events.ndjson`
- `<调用时间>_<环境名>_<id>_result.html`

## 重新渲染 HTML

```bash
python3 dify_aihcare_diet_runner.py render-html --record "userinput/未知患者_饮食方案_20260519-101112/20260519-102000_msg-1/20260519-102000_msg-1_raw-result.json"
python3 dify_aihcare_sport_runner.py render-html --record "userinput/未知患者_运动方案_20260519-101112/20260519-102000_msg-1/20260519-102000_msg-1_raw-result.json"
python3 dify_aihcare_followup_review_runner.py render-html --record "userinput/未知患者_复诊复查指导_20260519-101112/20260519-102000_msg-1/20260519-102000_msg-1_raw-result.json"
python3 dify_aihcare_health_weekly_report_runner.py render-html --record "userinput/未知患者_健康周报_20260519-101112/20260519-102000_msg-1/20260519-102000_msg-1_raw-result.json"
```

## 本地测试

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程"
python3 -m unittest discover demo/tests
python3 -m py_compile demo/*.py demo/tests/*.py
```
