# AI 健管师第一期自然语言查询 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成一个 AgentScope 2.x 查询服务，让健管师通过自然语言找到有权限的患者并读取慢管系统患者档案，同时在歧义、超范围或接口不支持时给出可执行选择。

**Architecture:** 新建独立 Python/FastAPI 后端。AgentScope ReActAgent 负责理解指令、制定查询计划和选择只读 Tool；业务 Harness 负责可信会话上下文、计划校验、身份注入、用户介入、来源登记和结果返回。第一期只返回患者与原始健康材料，不做摘要、问题发现、管理建议或交付物生成。

**Tech Stack:** Python 3.11、AgentScope 2.x、FastAPI、Pydantic 2、httpx、pytest、respx

---

## 范围红线

- 允许：患者搜索、人群筛选、档案及健康材料查询、连续追问、结构化用户介入。
- 禁止：患者问题判断、健康摘要、管理建议、成果物、慢管写操作、定时扫描。
- 所有慢管接口只能从后端调用；模型不得接触账号、密码、Token、租户 ID 或机构 ID。
- 语义条件如“控制不好”“值得干预”只能被识别为第二期分析需求；第一期返回可查询材料或替代选项，不输出判断。

## 文件结构

```text
【专项】健管师Agent/backend/
├── pyproject.toml
├── .env.example
├── src/aihcare_agent/
│   ├── __init__.py
│   ├── config.py                 # 环境配置
│   ├── schemas.py                # 查询计划、动作、上下文和返回协议
│   ├── chronic_client.py         # 登录、Token 缓存和慢管 HTTP 调用
│   ├── source_registry.py        # 原始来源登记
│   ├── tools.py                  # 九个 AgentScope 只读 Tool
│   ├── tool_guard.py             # 身份注入、参数校验、限流和脱敏
│   ├── planner.py                # ReActAgent、Prompt 和 Structured Output
│   ├── plan_policy.py            # 计划校验及继续/询问/停止规则
│   ├── sessions.py               # 连续指代和 resume token
│   ├── service.py                # 查询编排
│   └── api.py                    # FastAPI 接口
└── tests/
    ├── conftest.py
    ├── test_schemas.py
    ├── test_chronic_client.py
    ├── test_source_registry.py
    ├── test_tools.py
    ├── test_plan_policy.py
    ├── test_sessions.py
    └── test_api.py
```

## Task 1: 初始化独立 Python 服务

**Files:**
- Create: `【专项】健管师Agent/backend/pyproject.toml`
- Create: `【专项】健管师Agent/backend/.env.example`
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/__init__.py`
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/config.py`
- Test: `【专项】健管师Agent/backend/tests/test_config.py`

- [ ] **Step 1: 写配置失败测试**

```python
from aihcare_agent.config import Settings


def test_settings_require_server_side_chronic_credentials(monkeypatch):
    monkeypatch.setenv("CHRONIC_API_BASE", "https://example.test")
    monkeypatch.setenv("CHRONIC_TENANT_ID", "tenant")
    monkeypatch.setenv("CHRONIC_ORG_ID", "org")
    monkeypatch.setenv("CHRONIC_LOGIN_ID", "manager")
    monkeypatch.setenv("CHRONIC_LOGIN_PASSWORD", "secret")
    settings = Settings()
    assert settings.chronic_api_base == "https://example.test"
    assert settings.max_candidates == 50
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd '【专项】健管师Agent/backend' && python -m pytest tests/test_config.py -v`

Expected: FAIL，提示 `aihcare_agent.config` 不存在。

- [ ] **Step 3: 创建项目和最小配置**

```toml
[project]
name = "aihcare-health-manager-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "agentscope>=2.0.3,<2.1",
  "fastapi>=0.116,<1",
  "uvicorn>=0.35,<1",
  "httpx>=0.28,<1",
  "pydantic>=2.11,<3",
  "pydantic-settings>=2.10,<3"
]

[project.optional-dependencies]
test = ["pytest>=8.4,<9", "pytest-asyncio>=1.1,<2", "respx>=0.22,<1"]

[tool.pytest.ini_options]
pythonpath = ["src"]
asyncio_mode = "auto"
```

```python
# src/aihcare_agent/config.py
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    chronic_api_base: str
    chronic_tenant_id: str
    chronic_org_id: str
    chronic_login_id: str
    chronic_login_password: SecretStr
    dashscope_api_key: SecretStr | None = None
    model_name: str = "qwen-max"
    max_candidates: int = 50
    max_tool_calls: int = 12
    request_timeout_seconds: float = 20.0
```

`.env.example` 只写变量名和示例占位值，不复制接口文档中的真实凭证。

- [ ] **Step 4: 安装依赖并运行测试**

Run: `cd '【专项】健管师Agent/backend' && python -m pip install -e '.[test]' && python -m pytest tests/test_config.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend'
git commit -m "chore: scaffold health manager query service"
```

## Task 2: 定义第一期协议

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/schemas.py`
- Test: `【专项】健管师Agent/backend/tests/test_schemas.py`

- [ ] **Step 1: 写协议测试**

```python
from typing import get_args
from aihcare_agent.schemas import QueryPlan, QueryRequest, NextAction


def test_query_plan_separates_supported_filters_from_semantic_conditions():
    plan = QueryPlan(
        task_type="find_patients",
        structured_filters={"riskMark": "red"},
        semantic_conditions=["blood_pressure_not_well_controlled"],
        planned_tools=["search_managed_patients"],
    )
    assert plan.semantic_conditions == ["blood_pressure_not_well_controlled"]


def test_request_never_accepts_trusted_identity_from_user_body():
    request = QueryRequest(message="看看这个患者", session_id="s1")
    assert not hasattr(request, "tenant_id")


def test_next_action_is_closed_union():
    assert set(get_args(NextAction)) == {"call_tool", "ask_user", "answer", "stop"}
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_schemas.py -v`

Expected: FAIL，提示协议类型不存在。

- [ ] **Step 3: 实现最小协议**

```python
from typing import Any, Literal
from pydantic import BaseModel, Field

NextAction = Literal["call_tool", "ask_user", "answer", "stop"]


class TrustedContext(BaseModel):
    tenant_id: str
    org_id: str
    health_manager_id: str
    current_patient_id: str | None = None


class QueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str
    resume_token: str | None = None
    selected_option_id: str | None = None


class QueryPlan(BaseModel):
    task_type: Literal["find_patient", "find_patients", "get_patient_material", "continue_query"]
    patient_selector: dict[str, Any] = Field(default_factory=dict)
    structured_filters: dict[str, Any] = Field(default_factory=dict)
    semantic_conditions: list[str] = Field(default_factory=list)
    time_range: dict[str, Any] | None = None
    planned_tools: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    limit: int | None = None


class InterventionOption(BaseModel):
    id: str
    label: str


class AgentTurn(BaseModel):
    next_action: NextAction
    plan: QueryPlan | None = None
    reason_code: str | None = None
    question: str | None = None
    options: list[InterventionOption] = Field(default_factory=list)
    tool_name: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    purpose: str | None = None
    result: dict[str, Any] | None = None
```

- [ ] **Step 4: 运行协议测试**

Run: `python -m pytest tests/test_schemas.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/schemas.py' '【专项】健管师Agent/backend/tests/test_schemas.py'
git commit -m "feat: define phase one query contracts"
```

## Task 3: 实现慢管鉴权和 HTTP 客户端

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/chronic_client.py`
- Test: `【专项】健管师Agent/backend/tests/test_chronic_client.py`

- [ ] **Step 1: 用 respx 写登录、缓存和单次重试测试**

测试必须覆盖：登录请求带租户和机构 Header；业务请求带 Bearer Token；401 后只重新登录并重试一次；日志和异常文本不包含密码或 Token。

```python
@pytest.mark.asyncio
async def test_business_request_reauthenticates_only_once(client, respx_mock):
    login = respx_mock.post("https://example.test/org-api/auth/login").mock(
        side_effect=[
            httpx.Response(200, json={"code": 0, "data": {"accessToken": "t1", "expiresTime": 1}}),
            httpx.Response(200, json={"code": 0, "data": {"accessToken": "t2", "expiresTime": 9999999999999}}),
        ]
    )
    archive = respx_mock.get("https://example.test/org-api/cdm/patient-icpr/basic-archive").mock(
        side_effect=[httpx.Response(401), httpx.Response(200, json={"code": 0, "data": {"id": "p1"}})]
    )
    result = await client.get_basic_archive("p1")
    assert result["id"] == "p1"
    assert login.call_count == 2
    assert archive.call_count == 2
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_chronic_client.py -v`

Expected: FAIL，提示 `ChronicCareClient` 不存在。

- [ ] **Step 3: 实现客户端**

实现 `ChronicCareClient`，集中封装 Header、Token 缓存、业务码检查、超时和一次重试。提供九个方法：`search_managed_patients`、`search_indicator_updates`、`get_basic_archive`、`get_chronic_archive`、`get_recent_indicators`、`get_medication_summary`、`get_medication_detail`、`get_diet_records`、`get_sport_records`。

所有方法返回 `data`，并把 HTTP 状态、业务码和链路 ID放入专用异常；异常 `__str__` 只输出脱敏信息。

- [ ] **Step 4: 运行客户端测试**

Run: `python -m pytest tests/test_chronic_client.py -v`

Expected: PASS，且九个接口的请求方法、路径和参数测试全部通过。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/chronic_client.py' '【专项】健管师Agent/backend/tests/test_chronic_client.py'
git commit -m "feat: add read-only chronic care client"
```

## Task 4: 登记原始来源

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/source_registry.py`
- Test: `【专项】健管师Agent/backend/tests/test_source_registry.py`

- [ ] **Step 1: 写不可变来源和哈希测试**

```python
def test_register_source_is_content_addressed(registry):
    first = registry.register("chronic_api", "p1", {"value": 120})
    second = registry.register("chronic_api", "p1", {"value": 120})
    assert first.content_hash == second.content_hash
    assert first.source_id != second.source_id
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_source_registry.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现内存接口和持久化抽象**

定义 `SourceRecord` 和 `SourceRegistry` 协议；第一期提供 `InMemorySourceRegistry` 供 Demo 和测试使用。记录来源类型、患者 ID、读取时间、内容哈希和原始内容；`SourceRecord.to_agent_json()` 只序列化 `source_id`、来源类型、患者 ID、读取时间和受控内容。生产接入时可替换数据库实现而不改变 Tool。

- [ ] **Step 4: 运行测试**

Run: `python -m pytest tests/test_source_registry.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/source_registry.py' '【专项】健管师Agent/backend/tests/test_source_registry.py'
git commit -m "feat: register chronic query sources"
```

## Task 5: 封装九个 AgentScope 只读 Tool

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/tools.py`
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/tool_guard.py`
- Test: `【专项】健管师Agent/backend/tests/test_tools.py`

- [ ] **Step 1: 写工具安全测试**

覆盖：工具 schema 不包含 Token、租户或机构；患者查询自动绑定当前健管师；每个成功结果都生成 `source_id`；饮食运动日期透传一致；取药结果不会被工具包装成“实际服药”。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_tools.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现工具工厂**

```python
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock


def build_readonly_toolkit(client, registry, trusted_context) -> Toolkit:
    toolkit = Toolkit()

    async def search_managed_patients(keyword: str = "", page_no: int = 1, page_size: int = 20) -> ToolResponse:
        """查询当前健管师有权限管理的患者候选。

        仅用于姓名或手机号查找和候选患者筛选。返回候选不表示患者存在健康问题。
        不能判断控制情况、依从性或是否需要干预。
        """
        data = await client.search_managed_patients(
            keyword=keyword,
            manager_ids=[trusted_context.health_manager_id],
            page_no=page_no,
            page_size=page_size,
        )
        source = registry.register("chronic_api", None, data)
        return ToolResponse(content=[TextBlock(type="text", text=source.to_agent_json())])

    toolkit.register_tool_function(search_managed_patients)
    toolkit.register_tool_function(search_indicator_updates)
    toolkit.register_tool_function(get_basic_archive)
    toolkit.register_tool_function(get_chronic_archive)
    toolkit.register_tool_function(get_recent_indicators)
    toolkit.register_tool_function(get_medication_summary)
    toolkit.register_tool_function(get_medication_detail)
    toolkit.register_tool_function(get_diet_records)
    toolkit.register_tool_function(get_sport_records)
    return toolkit
```

在同一文件中显式定义八个函数；参数与客户端方法严格对应：

| 函数 | 参数 |
| --- | --- |
| `search_indicator_updates` | `create_time_start`、`create_time_end`、可选指标类型、可选数据来源、页码、页大小 |
| `get_basic_archive` | `patient_id` |
| `get_chronic_archive` | `patient_id` |
| `get_recent_indicators` | `patient_id` |
| `get_medication_summary` | `patient_id`、可选药品名、页码、页大小 |
| `get_medication_detail` | `patient_id`、药品名、厂家、规格、页码、页大小 |
| `get_diet_records` | `patient_id`、开始日期、结束日期 |
| `get_sport_records` | `patient_id`、开始日期、结束日期 |

每个函数执行固定三步：调用对应 `ChronicCareClient` 方法、使用 `registry.register()` 登记结果、返回只含 `source_id` 和受控数据的 `ToolResponse`。每个函数写完整独立 docstring，并逐项包含设计文档第 5.5 节的能力、禁止用途、调用条件、返回语义和限制。

- [ ] **Step 4: 加入 Tool Middleware**

Middleware 检查页大小、日期范围、患者 ID、调用次数和当前会话授权患者集合；超限时跳过实际执行并返回稳定错误码。模型输入中的可信身份字段一律丢弃。

- [ ] **Step 5: 运行工具测试**

Run: `python -m pytest tests/test_tools.py -v`

Expected: PASS，九个 Tool 均被注册且安全测试通过。

- [ ] **Step 6: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/tools.py' '【专项】健管师Agent/backend/src/aihcare_agent/tool_guard.py' '【专项】健管师Agent/backend/tests/test_tools.py'
git commit -m "feat: expose guarded chronic query tools"
```

## Task 6: 实现查询计划校验和用户介入策略

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/plan_policy.py`
- Test: `【专项】健管师Agent/backend/tests/test_plan_policy.py`

- [ ] **Step 1: 写决策表测试**

```python
@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("duplicate_patient_names", "ask_user"),
        ("scope_too_large", "ask_user"),
        ("unsupported_semantic_filter", "ask_user"),
        ("goal_satisfied", "answer"),
        ("tool_budget_exhausted", "stop"),
        ("more_authorized_data_needed", "call_tool"),
    ],
)
def test_policy_actions(reason, expected, policy):
    assert policy.decide(reason).next_action == expected
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_plan_policy.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现 `PlanPolicy`**

实现设计文档中的九个原因码、四类下一步动作、低影响默认值、候选数上限、工具次数上限和语义条件一期降级。用户介入结果必须包含 2 至 3 个可执行选项；`AMBIGUOUS_PATIENT` 选项只展示最少消歧信息。

第一期遇到“控制不好”“值得干预”等条件时返回 `UNSUPPORTED_FILTER`，选项固定为：查询相关患者材料、缩小到具体患者、取消本次查询。

- [ ] **Step 4: 运行测试**

Run: `python -m pytest tests/test_plan_policy.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/plan_policy.py' '【专项】健管师Agent/backend/tests/test_plan_policy.py'
git commit -m "feat: enforce query plan intervention policy"
```

## Task 7: 配置 AgentScope 查询 Agent

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/planner.py`
- Test: `【专项】健管师Agent/backend/tests/test_planner.py`

- [ ] **Step 1: 写模型无关的规划器测试**

使用 FakeModel 验证：当前患者指令不会调用患者搜索；同名患者转成 `ask_user`；语义分析请求不会输出患者问题；连续追问能引用会话中的患者 ID。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_planner.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现 Agent 工厂**

使用 `ReActAgent`、`DashScopeChatModel`、`DashScopeChatFormatter`、`InMemoryMemory` 和 Task 5 Toolkit。系统提示词明确：第一期只查询和返回来源材料；每轮输出 `call_tool/ask_user/answer/stop`；不能总结健康状况、发现问题或提出管理意见；工具不支持时必须使用结构化介入。

Structured Output 使用 `AgentTurn`。业务 Harness 只接受通过 Pydantic 校验的结果，格式失败允许修正一次。

- [ ] **Step 4: 运行规划器测试**

Run: `python -m pytest tests/test_planner.py -v`

Expected: PASS，测试不调用真实模型。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/planner.py' '【专项】健管师Agent/backend/tests/test_planner.py'
git commit -m "feat: add AgentScope query planner"
```

## Task 8: 实现会话恢复和查询编排

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/sessions.py`
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/service.py`
- Test: `【专项】健管师Agent/backend/tests/test_sessions.py`

- [ ] **Step 1: 写恢复测试**

验证 `resumeToken` 不透明、带过期时间、绑定 session 和健管师；其他用户不能恢复；选择患者后从原计划继续，不重新执行已经成功的工具。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_sessions.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现 SessionStore 和 QueryService**

`QueryService.handle()` 注入 `TrustedContext`，运行 Planner，交给 `PlanPolicy` 校验，执行 Tool，并循环到 `ask_user/answer/stop`。循环次数使用配置上限；`answer` 只包含患者候选和来源材料，不生成健康摘要。

`SessionStore` 保存当前患者、候选患者 ID、来源 ID、已完成步骤和 Agent 状态；第一期提供内存实现，接口允许以后切换 Redis。

- [ ] **Step 4: 运行恢复测试**

Run: `python -m pytest tests/test_sessions.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/sessions.py' '【专项】健管师Agent/backend/src/aihcare_agent/service.py' '【专项】健管师Agent/backend/tests/test_sessions.py'
git commit -m "feat: orchestrate resumable patient queries"
```

## Task 9: 暴露 FastAPI 查询接口

**Files:**
- Create: `【专项】健管师Agent/backend/src/aihcare_agent/api.py`
- Test: `【专项】健管师Agent/backend/tests/test_api.py`
- Create: `【专项】健管师Agent/第一期查询接口协议.md`

- [ ] **Step 1: 写 API 测试**

覆盖：正常患者查询返回 `answer`；同名患者返回 `ask_user` 和选项；resume 后继续；用户请求体不能注入可信身份；慢管失败返回稳定原因码；响应不包含 Token 和密码。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/test_api.py -v`

Expected: FAIL。

- [ ] **Step 3: 实现接口**

提供 `POST /v1/health-manager/query`。可信租户、机构和健管师由已有慢管后端经过认证后写入请求上下文；Demo 可使用仅绑定本地环境的测试依赖，不从 JSON body 读取身份。

响应统一使用：

```json
{
  "nextAction": "answer",
  "sessionId": "s1",
  "message": "已找到患者并取得相关档案。",
  "patients": [],
  "materials": [],
  "options": [],
  "resumeToken": null,
  "limitations": []
}
```

接口协议文档给出 `answer`、`ask_user`、`stop` 三类前端可见示例，并明确第一期不返回 `patientProblems`、`managementAdvice` 或 `artifacts`。

- [ ] **Step 4: 运行 API 测试**

Run: `python -m pytest tests/test_api.py -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/aihcare_agent/api.py' '【专项】健管师Agent/backend/tests/test_api.py' '【专项】健管师Agent/第一期查询接口协议.md'
git commit -m "feat: expose health manager query API"
```

## Task 10: 端到端验收和运行文档

**Files:**
- Create: `【专项】健管师Agent/backend/tests/test_phase1_acceptance.py`
- Create: `【专项】健管师Agent/第一期运行与验收手册.md`

- [ ] **Step 1: 编写端到端验收测试**

至少覆盖以下指令：

1. “帮我查一下张三的健康档案”；
2. “看看这个患者最近的指标”；
3. “查我管理的高血压红标患者”；
4. “再看看第一个人的用药”；
5. 同名患者需要选择；
6. “找出血压控制不好的患者”降级为查询材料或缩小范围选项；
7. 日期不清、接口不支持、范围过大和部分接口失败；
8. 越权 patientId 被拒绝；
9. 输出中不含总结、患者问题、管理建议和成果物。

- [ ] **Step 2: 运行全部测试**

Run: `cd '【专项】健管师Agent/backend' && python -m pytest -v`

Expected: 全部 PASS；不访问真实慢管接口或真实模型。

- [ ] **Step 3: 添加受控真实联调步骤**

运行手册要求通过环境变量注入 Demo 凭证，只验证登录、单患者查询和脱敏日志。不得把返回的患者档案写入测试快照、提交到 Git 或展示在公开截图中。

- [ ] **Step 4: 执行静态范围检查**

Run: `rg -n "patientProblems|managementAdvice|artifacts|write_|create_|update_|delete_" '【专项】健管师Agent/backend/src'`

Expected: 除协议中的禁止字段说明外，无第二期、第三期或慢管写操作实现。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/tests/test_phase1_acceptance.py' '【专项】健管师Agent/第一期运行与验收手册.md'
git commit -m "test: verify phase one patient query flow"
```

## 完成标准

- 健管师能用自然语言查询单个患者或接口支持的人群；
- Agent 能形成并执行受控查询计划；
- 九个慢管只读 Tool 均有权限、来源、返回语义和限制测试；
- 同名、范围不清、语义分析需求、接口不支持和范围过大均返回可执行选项；
- 连续追问能复用当前患者和已查询材料；
- 所有查询结果可追踪到来源且日志脱敏；
- 第一期开启真实联调时不会输出患者问题、管理建议或交付物；
- 全部自动化测试通过，真实联调材料不进入 Git。
