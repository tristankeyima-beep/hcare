# AI 健管师第一期 Java 自然语言查询 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 AgentScope Java 建成自然语言患者查询服务，使健管师能找到授权患者并读取慢管档案，在歧义或能力不足时得到可执行选择。

**Architecture:** 新建独立 Maven/Spring Boot 模块。AgentScope Java `ReActAgent` 负责理解指令、制定查询计划并选择只读工具；Spring 业务 Harness 负责可信身份、计划校验、权限、来源登记、用户介入和结果协议。第一期不启用 `HarnessAgent`、Workspace、健康摘要、问题发现、管理建议或成果物。

**Tech Stack:** JDK 17、Maven 3.9+、Spring Boot 3、Spring WebFlux/WebClient、AgentScope Java、Jackson、Reactor、JUnit 5、Mockito、WireMock

---

## 实施前版本校准

官方要求 JDK 17+、推荐 Maven 3.9+；仅需 ReAct 能力时使用 core/all-in-one AgentScope，第三期需要 Workspace、持久化和 sandbox 时再评估 `agentscope-harness`。实施会话开始时执行：

```bash
java -version
mvn -version
```

如果现有慢管 Java 服务已经有父 POM，Spring Boot、Jackson、Reactor 和测试依赖版本继承父 POM；AgentScope Java 使用团队依赖治理批准的稳定版本。独立验证模块以官方当前稳定版 `io.agentscope:agentscope:1.0.12` 为基线，升级时先运行本计划全部测试。

## 范围红线

- 允许：自然语言患者搜索、人群过滤、指定档案查询、连续指代、结构化用户介入。
- 禁止：健康摘要、患者问题、管理建议、成果物、慢管写操作、定时扫描、Workspace。
- 模型不得接触登录密码、Token、租户 ID、机构 ID或可信健管师身份。
- “控制不好”“值得干预”等第二期语义只触发能力说明和替代选项，不输出健康判断。

## 文件结构

```text
【专项】健管师Agent/backend/
├── pom.xml
├── src/main/java/com/gtmahmo/aihcare/agent/query/
│   ├── QueryApplication.java
│   ├── config/AgentQueryProperties.java
│   ├── domain/QueryContracts.java
│   ├── chronic/ChronicCareClient.java
│   ├── chronic/ChronicCareException.java
│   ├── source/SourceRegistry.java
│   ├── source/InMemorySourceRegistry.java
│   ├── tool/ChronicQueryTools.java
│   ├── policy/QueryPlanPolicy.java
│   ├── agent/QueryAgentFactory.java
│   ├── session/QuerySessionStore.java
│   ├── service/QueryOrchestrator.java
│   └── web/QueryController.java
├── src/main/resources/application.yml
└── src/test/java/com/gtmahmo/aihcare/agent/query/
    ├── chronic/ChronicCareClientTest.java
    ├── source/SourceRegistryTest.java
    ├── tool/ChronicQueryToolsTest.java
    ├── policy/QueryPlanPolicyTest.java
    ├── agent/QueryAgentFactoryTest.java
    ├── session/QuerySessionStoreTest.java
    └── web/QueryControllerTest.java
```

## Task 1: 初始化 Maven/Spring Boot 查询模块

**Files:**
- Create: `【专项】健管师Agent/backend/pom.xml`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/QueryApplication.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/config/AgentQueryProperties.java`
- Create: `【专项】健管师Agent/backend/src/main/resources/application.yml`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/QueryApplicationTest.java`

- [ ] **Step 1: 写启动失败测试**

```java
@SpringBootTest(properties = {
    "aihcare.agent.chronic-api-base=https://example.test",
    "aihcare.agent.tenant-id=tenant",
    "aihcare.agent.org-id=org",
    "aihcare.agent.login-id=manager",
    "aihcare.agent.login-password=secret"
})
class QueryApplicationTest {
    @Test void contextLoads() {}
}
```

- [ ] **Step 2: 运行并确认失败**

Run: `cd '【专项】健管师Agent/backend' && mvn -q -Dtest=QueryApplicationTest test`

Expected: FAIL，项目或启动类不存在。

- [ ] **Step 3: 创建 Maven 项目**

`pom.xml` 使用 Java 17，加入 `spring-boot-starter-webflux`、`spring-boot-starter-validation`、`io.agentscope:agentscope:1.0.12`、`spring-boot-starter-test`、`reactor-test` 和 WireMock。`application.yml` 只引用环境变量，不写真实凭证：

```yaml
aihcare:
  agent:
    chronic-api-base: ${CHRONIC_API_BASE}
    tenant-id: ${CHRONIC_TENANT_ID}
    org-id: ${CHRONIC_ORG_ID}
    login-id: ${CHRONIC_LOGIN_ID}
    login-password: ${CHRONIC_LOGIN_PASSWORD}
    model-name: ${AGENT_MODEL_NAME:qwen-max}
    max-candidates: 50
    max-tool-calls: 12
    request-timeout: 20s
```

用 `@ConfigurationProperties(prefix = "aihcare.agent")` 定义不可变配置 record；密码使用 `char[]` 或受控字符串且禁止进入 `toString()`。

- [ ] **Step 4: 运行测试**

Run: `mvn -q -Dtest=QueryApplicationTest test`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend'
git commit -m "chore: scaffold Java health manager query service"
```

## Task 2: 定义查询计划与用户介入协议

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/domain/QueryContracts.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/domain/QueryContractsTest.java`

- [ ] **Step 1: 写 Jackson 协议测试**

```java
@Test
void queryPlanKeepsSemanticConditionsSeparate() throws Exception {
    QueryPlan plan = new QueryPlan(
            TaskType.FIND_PATIENTS,
            Map.of(),
            Map.of("riskMark", "red"),
            List.of("blood_pressure_not_well_controlled"),
            null,
            List.of("search_managed_patients"),
            List.of(),
            List.of(),
            10);
    String json = objectMapper.writeValueAsString(plan);
    assertThat(json).contains("semanticConditions");
}

@Test
void userRequestCannotCarryTrustedTenantIdentity() {
    assertThat(Arrays.stream(QueryRequest.class.getRecordComponents())
            .map(RecordComponent::getName))
            .doesNotContain("tenantId", "orgId", "healthManagerId");
}
```

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=QueryContractsTest test`

Expected: FAIL，协议类型不存在。

- [ ] **Step 3: 实现 Java records 和枚举**

定义：`TrustedContext`、`QueryRequest`、`QueryPlan`、`TaskType`、`NextAction(CALL_TOOL, ASK_USER, ANSWER, STOP)`、`InterventionOption`、`AgentTurn`、`PatientCandidate`、`MaterialResult`、`QueryResponse`。所有集合使用非空默认值；`QueryRequest` 仅包含消息、会话 ID、恢复令牌和选择项。

- [ ] **Step 4: 运行协议测试**

Run: `mvn -q -Dtest=QueryContractsTest test`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/domain' '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/domain'
git commit -m "feat: define Java phase one query contracts"
```

## Task 3: 实现慢管 WebClient 与鉴权

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/chronic/ChronicCareClient.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/chronic/ChronicCareException.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/chronic/ChronicCareClientTest.java`

- [ ] **Step 1: 写 WireMock 测试**

覆盖登录 Header、Bearer Token、Token 缓存、401 后只重新登录并重试一次、业务码错误、超时及脱敏异常。断言请求和日志中不会输出密码或 Token。

```java
@Test
void reauthenticatesOnlyOnceAfterUnauthorized() {
    stubFor(post("/org-api/auth/login")
            .inScenario("reauth")
            .whenScenarioStateIs(STARTED)
            .willReturn(okJson(loginJson("t1")))
            .willSetStateTo("second"));
    stubFor(get(urlPathEqualTo("/org-api/cdm/patient-icpr/basic-archive"))
            .inScenario("archive")
            .whenScenarioStateIs(STARTED)
            .willReturn(unauthorized())
            .willSetStateTo("retry"));
    stubFor(get(urlPathEqualTo("/org-api/cdm/patient-icpr/basic-archive"))
            .inScenario("archive")
            .whenScenarioStateIs("retry")
            .willReturn(okJson("{\"code\":0,\"data\":{\"patientId\":\"p1\"}}")));
    assertThat(client.getBasicArchive("p1").block()).containsEntry("patientId", "p1");
}
```

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=ChronicCareClientTest test`

Expected: FAIL。

- [ ] **Step 3: 实现九个只读方法**

使用 Spring `WebClient` 集中注入租户和机构 Header。提供：`searchManagedPatients`、`searchIndicatorUpdates`、`getBasicArchive`、`getChronicArchive`、`getRecentIndicators`、`getMedicationSummary`、`getMedicationDetail`、`getDietRecords`、`getSportRecords`，返回 `Mono<JsonNode>`。登录密码与 Token 只存在客户端内部。

- [ ] **Step 4: 运行测试**

Run: `mvn -q -Dtest=ChronicCareClientTest test`

Expected: PASS，九个路径、方法、参数和异常分支均通过。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/chronic' '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/chronic'
git commit -m "feat: add reactive chronic care client"
```

## Task 4: 登记来源并封装九个 AgentScope Java Tool

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/source/SourceRegistry.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/source/InMemorySourceRegistry.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/tool/ChronicQueryTools.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/tool/ChronicQueryToolsTest.java`

- [ ] **Step 1: 写 Tool 契约测试**

验证九个 `@Tool` 方法均 `readOnly=true`；schema 不含 Token、租户、机构和健管师；当前健管师从 `RuntimeContext` 注入；成功返回含 `sourceId`；“有上传”“取药”“饮食/运动记录”不被工具包装为异常、实际服药或真实行为结论。

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=ChronicQueryToolsTest test`

Expected: FAIL。

- [ ] **Step 3: 实现来源登记**

`SourceRegistry.register(sourceType, patientId, JsonNode)` 返回不可变 `SourceRecord`，包含 UUID、类型、患者、读取时间、SHA-256 和原始内容。`toAgentJson()` 只输出受控字段。内存实现用于一期 Demo；接口允许替换数据库。

- [ ] **Step 4: 实现反射式 Java Tool**

在 `ChronicQueryTools` 中为九个方法使用 `io.agentscope.core.tool.Tool` 和 `ToolParam`。示例：

```java
@Tool(
    name = "get_basic_archive",
    description = "获取当前授权患者的基础档案。返回慢管系统档案快照，不表示患者当前存在健康问题。",
    readOnly = true,
    concurrencySafe = true)
public Mono<String> getBasicArchive(
        @ToolParam(name = "patientId", description = "经过权限校验的患者ID") String patientId,
        TrustedContext context) {
    guard.assertPatientAllowed(patientId, context);
    return client.getBasicArchive(patientId)
            .map(data -> registry.register("chronic_api", patientId, data).toAgentJson());
}
```

其余八个方法逐项采用设计文档第 5.5 节的能力、禁止用途、调用条件、返回语义和限制。注册方式：

```java
Toolkit toolkit = new Toolkit();
toolkit.registerTool(new ChronicQueryTools(client, registry, guard));
```

使用 User POJO 注入 `TrustedContext`，使其不进入 LLM 参数 schema；工具内部再次执行患者范围校验。对于需要更细权限控制的工具，升级为 `ToolBase` 并实现 `checkPermissions`。

- [ ] **Step 5: 运行 Tool 测试**

Run: `mvn -q -Dtest=ChronicQueryToolsTest test`

Expected: PASS，九个 Tool 可注册且安全断言通过。

- [ ] **Step 6: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/source' '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/tool' '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/tool'
git commit -m "feat: expose guarded AgentScope Java query tools"
```

## Task 5: 实现查询计划与用户介入策略

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/policy/QueryPlanPolicy.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/policy/QueryPlanPolicyTest.java`

- [ ] **Step 1: 写参数化决策测试**

```java
@ParameterizedTest
@CsvSource({
    "AMBIGUOUS_PATIENT,ASK_USER",
    "AMBIGUOUS_SCOPE,ASK_USER",
    "UNSUPPORTED_FILTER,ASK_USER",
    "GOAL_SATISFIED,ANSWER",
    "TOOL_BUDGET_EXHAUSTED,STOP",
    "MORE_AUTHORIZED_DATA_NEEDED,CALL_TOOL"
})
void appliesDecisionTable(String reason, NextAction expected) {
    assertThat(policy.decide(reason).nextAction()).isEqualTo(expected);
}
```

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=QueryPlanPolicyTest test`

Expected: FAIL。

- [ ] **Step 3: 实现规则**

实现九个用户介入原因码、四类动作、候选数和工具次数上限、低影响默认值及一期语义条件降级。`ASK_USER` 必须返回 2 至 3 个可执行选项；同名患者仅展示最少消歧信息。计划不得扩大到新租户、机构或未授权患者。

- [ ] **Step 4: 运行测试**

Run: `mvn -q -Dtest=QueryPlanPolicyTest test`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/policy' '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/policy'
git commit -m "feat: enforce Java query intervention policy"
```

## Task 6: 配置 AgentScope Java ReActAgent

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/agent/QueryAgentFactory.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/agent/QueryAgentFactoryTest.java`

- [ ] **Step 1: 写假模型测试**

测试当前患者指令不重复搜索、同名患者输出 `ASK_USER`、语义分析请求不输出患者问题、连续追问保留患者引用、达到工具上限输出 `STOP`。测试使用 AgentScope 测试模型或自定义 fake model，不调用真实大模型。

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=QueryAgentFactoryTest test`

Expected: FAIL。

- [ ] **Step 3: 构建 ReActAgent**

```java
ReActAgent agent = ReActAgent.builder()
        .name("health-manager-query-agent")
        .sysPrompt(promptLoader.phaseOneQueryPrompt())
        .model(model)
        .toolkit(toolkit)
        .build();
```

系统提示词要求每轮仅选择 `CALL_TOOL/ASK_USER/ANSWER/STOP`，第一期只查询和返回来源材料，禁止摘要、问题发现、管理意见和成果物。Java record/Jackson schema约束 `AgentTurn`；反序列化失败允许修正一次。

- [ ] **Step 4: 运行测试**

Run: `mvn -q -Dtest=QueryAgentFactoryTest test`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/agent' '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/agent'
git commit -m "feat: add AgentScope Java query agent"
```

## Task 7: 实现会话、编排与 Spring WebFlux API

**Files:**
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/session/QuerySessionStore.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/service/QueryOrchestrator.java`
- Create: `【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/web/QueryController.java`
- Test: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/web/QueryControllerTest.java`
- Create: `【专项】健管师Agent/第一期查询接口协议.md`

- [ ] **Step 1: 写 WebTestClient 测试**

覆盖正常查询、同名选择、恢复继续、可信身份不能由 JSON 注入、越权患者拒绝、慢管失败原因码、响应不含凭证、语义分析请求只返回一期选项。

- [ ] **Step 2: 运行并确认失败**

Run: `mvn -q -Dtest=QueryControllerTest test`

Expected: FAIL。

- [ ] **Step 3: 实现会话和编排**

`QuerySessionStore` 保存当前患者、候选 ID、来源 ID、已完成步骤和过期的恢复令牌；接口允许未来替换 Redis。`QueryOrchestrator` 使用 Reactor 串联 Agent、Policy 和 Tool，循环直到 `ASK_USER/ANSWER/STOP`，并执行最大工具步数限制。

- [ ] **Step 4: 实现 API**

提供 `POST /v1/health-manager/query`。可信身份从慢管后端认证上下文解析，不接受请求体身份。响应包含 `nextAction`、`sessionId`、患者、材料、选项、恢复令牌和局限说明；不包含患者问题、管理建议或成果物。

- [ ] **Step 5: 运行测试**

Run: `mvn -q -Dtest=QueryControllerTest test`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/session' '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/service' '【专项】健管师Agent/backend/src/main/java/com/gtmahmo/aihcare/agent/query/web' '【专项】健管师Agent/第一期查询接口协议.md'
git commit -m "feat: expose reactive health manager query API"
```

## Task 8: 端到端验收与真实联调手册

**Files:**
- Create: `【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/PhaseOneAcceptanceTest.java`
- Create: `【专项】健管师Agent/第一期运行与验收手册.md`

- [ ] **Step 1: 编写端到端测试**

使用 fake model 和 WireMock 覆盖：按姓名查档案、当前患者查指标、人群结构化过滤、继续查看第一个人的用药、同名消歧、语义条件一期降级、范围过大、部分接口失败、越权拒绝，以及输出不含第二/三期字段。

- [ ] **Step 2: 运行全部测试**

Run: `cd '【专项】健管师Agent/backend' && mvn -q test`

Expected: BUILD SUCCESS；不访问真实模型或真实慢管接口。

- [ ] **Step 3: 执行依赖与范围检查**

Run: `mvn -q dependency:tree`

Expected: AgentScope、Spring 和 Reactor 无冲突版本。

Run: `rg -n 'patientProblems|managementAdvice|artifacts|HarnessAgent|workspace|create|update|delete' src/main`

Expected: 除禁止项提示文案外，没有第二期、第三期、Workspace 或慢管写操作实现。

- [ ] **Step 4: 编写受控真实联调说明**

运行手册要求凭证通过环境变量或密钥服务注入，只验证登录、患者搜索、单患者档案和脱敏日志；不得把患者档案写入测试快照、Git、公开日志或截图。

- [ ] **Step 5: 提交**

```bash
git add '【专项】健管师Agent/backend/src/test/java/com/gtmahmo/aihcare/agent/query/PhaseOneAcceptanceTest.java' '【专项】健管师Agent/第一期运行与验收手册.md'
git commit -m "test: verify Java phase one patient queries"
```

## 完成标准

- 自然语言可以查询单个患者、接口支持的人群以及指定患者材料；
- ReActAgent 能形成受控查询路径并调用九个只读 Java Tool；
- 身份通过 RuntimeContext/User POJO 注入，不进入 LLM tool schema；
- 同名、范围不清、接口不支持和范围过大均返回可执行选项；
- 连续追问能够复用当前患者和来源；
- 全部查询可追踪、日志脱敏、401 只重试一次；
- 第一期不包含摘要、患者问题、管理建议、成果物、Workspace 或慢管写接口；
- `mvn test` 全部通过，真实联调数据不进入 Git。
