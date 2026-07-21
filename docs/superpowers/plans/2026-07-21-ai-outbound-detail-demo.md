# AI 外呼执行信息与 AI 标识 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 AI 语音随访结果详情静态 Demo 中展示 JobGroup、Job 和两次 Task 的阿里云执行过程，并明确区分原始回收数据与 AI 生成内容。

**Architecture:** 保持单页 `index.html` 架构。在随访结果总览之前插入可展开的执行信息卡，并复用页面现有的静态数据和原生 DOM 事件实现展开交互；通过统一 `AI` 角标类标识所有慢管侧 AI 归纳区块。结构测试继续只读取 HTML 静态内容，防止关键字段与边界文案回归。

**Tech Stack:** Vanilla HTML、CSS、JavaScript、Node.js 内置测试运行器、既有 ECharts 与 GSAP CDN。

---

## File Structure

| 文件 | 职责 |
| --- | --- |
| `【专项】智能外呼/AI语音随访结果详情页Demo/index.html` | 新增阿里云执行信息、Task 列表、原始数据标识和 AI 角标，并实现展开交互。 |
| `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs` | 断言 JobGroup、Job、两次 Task、原始数据与 AI 标识存在。 |

## Task 1：补充失败的结构测试

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs`

- [ ] 新增测试，要求页面包含下列真实演示字段：

```js
test("页面展示阿里云 JobGroup、Job、Task 执行链路", () => {
  const required = [
    "AI 外呼执行信息",
    "JobGroupId",
    "JobId",
    "Task_001",
    "Task_002",
    "首次外呼未接通",
    "第二次外呼接通并完成",
    "阿里云处理时间线",
    "阿里云原始回收数据",
    "toggleOutboundExecution",
  ];
  for (const value of required) assert.match(html, new RegExp(value));
});
```

- [ ] 运行下列命令，确认页面尚未包含这些字段而失败：

```bash
node --test "【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs"
```

预期：新增测试失败，现有测试通过。

## Task 2：实现执行信息与 Task 列表

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`

- [ ] 在“随访结果总览”之前插入 `id="outbound-execution"` 的内容卡。收起态展示外呼状态、场景、`JobGroupId`、`JobId`、结果同步时间；展开态展示处理时间线和两条 Task 表格。
- [ ] 使用以下固定演示数据：

```text
JobGroupId: jg-diabetes-20260715-001
JobId: job-followup-zhangcuili-001
Task_001: 10:00:00 首次拨打，NoAnswer，振铃 25 秒
Task_002: 10:06:00 接通完成，SucceededFinish，通话 4 分 38 秒
```

- [ ] 加入 `toggleOutboundExecution()`，通过 `aria-expanded` 和 `hidden` 控制时间线及 Task 列表的展开状态；录音按钮只显示“录音临时地址由后端按需获取”的静态提示。
- [ ] 新增页面样式，使执行状态、ID、时间线、Task 结果和录音入口在桌面及窄屏下可读。

## Task 3：标识原始数据与 AI 生成内容

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`
- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs`

- [ ] 新增统一的 `AI` 角标样式，并将角标放在“AI 随访小结”“基本信息评价”“需要进一步关注的点”“建议下一步动作”“AI 抽取依据”和 AI 线索图标题旁。
- [ ] 在通话证据区域标注“阿里云原始回收数据”，保留通话详情、完整对话、录音和标签为无 AI 角标内容。
- [ ] 在 AI 小结区保留“基于原始通话数据生成，待健管师核验”的边界说明。
- [ ] 新增测试，断言上述区块存在至少六个 `AI` 角标，以及原始数据标识和核验说明：

```js
test("页面明确区分原始数据与 AI 生成内容", () => {
  assert.match(html, /阿里云原始回收数据/);
  assert.match(html, /基于原始通话数据生成，待健管师核验/);
  assert.ok((html.match(/class="ai-badge"/g) || []).length >= 6);
});
```

## Task 4：验证

**Files:**

- Verify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`
- Verify: `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs`

- [ ] 运行结构测试：

```bash
node --test "【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs"
```

预期：全部通过。

- [ ] 启动静态服务，用浏览器检查：执行信息收起/展开、两次 Task 内容、AI 角标、原始数据标识、现有线索图与证据页签。
- [ ] 运行格式检查：

```bash
git diff --check -- "【专项】智能外呼/AI语音随访结果详情页Demo"
```

预期：无输出。

不创建提交：当前工作区已有用户未提交变更，且本次未被要求提交。
