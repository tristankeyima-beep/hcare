# AI 语音随访线索拓扑交互版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有随访结果详情页中加入可展开的 AI 线索拓扑、跨区域联动和待办展开交互，并更新患者与管理医生资料。

**Architecture:** 保留单页 `index.html`，通过固定版本 CDN 加载 ECharts graph 与 GSAP。页面以统一 `clueId` 连接总览卡、拓扑节点、关注点、完整对话和待办；ECharts 负责图布局、tooltip 与节点事件，GSAP 负责逐层展开和 DOM 联动高亮。脚本加载失败时显示 HTML 降级线路图。

**Tech Stack:** Vanilla HTML、CSS、JavaScript、Apache ECharts 5.6、GSAP 3、Node.js 内置测试运行器、Playwright CLI。

---

## File Structure

| 文件 | 职责 |
| --- | --- |
| `【专项】智能外呼/AI语音随访结果详情页Demo/index.html` | 患者结果详情、AI 线索拓扑、证据页签和待办展开交互。 |
| `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs` | 患者资料、图表依赖、关键交互函数和医疗边界回归测试。 |
| `【专项】智能外呼/AI语音随访结果详情页Demo/INTERACTION_DESIGN.md` | 已确认的 A 方案交互设计。 |

### Task 1: 更新测试约束

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs`

- [ ] 写入患者资料断言：张翠丽、女、61 岁、1964-09-12、于磊磊、糖尿病代谢病科(泰安市中心医院)。
- [ ] 写入交互断言：`followup-journey-chart`、`playJourney`、`expandJourney`、`focusJourneyNode`、`toggleActionItem`、ECharts 和 GSAP 脚本引用。
- [ ] 运行 `node --test '【专项】智能外呼/AI语音随访结果详情页Demo/test/structure.test.mjs'`，确认因现有页面缺少上述内容而失败。

### Task 2: 更新患者资料与交互语义

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`

- [ ] 更新患者姓名、性别、年龄、出生日期和管理医生信息，同时替换对话中的患者称呼。
- [ ] 将总览卡改为可点击按钮并绑定 `data-focus-node`，保留键盘焦点样式和语义色。
- [ ] 将待办卡改为可展开按钮，加入核验清单和 `aria-expanded`。
- [ ] 运行结构测试，确认患者资料和静态交互标记通过。

### Task 3: 实现线索拓扑和跨区域联动

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`

- [ ] 引入 ECharts 5.6 与 GSAP 3 固定版本 CDN。
- [ ] 创建 `journeyNodes` 与 `journeyLinks`；每个节点定义 `id`、`parentId`、`stage`、`time`、`summary`、`quote`、`confidence` 和 `targetSelector`。
- [ ] 实现 `renderJourney()`，根据 `expandedNodeIds` 过滤可见节点与连线，并使用 graph `layout: 'none'` 保持讲解顺序。
- [ ] 实现 `focusJourneyNode(nodeId)`：展开祖先路径、选中节点、更新详情面板、通过 GSAP 高亮相关正文卡片。
- [ ] 实现 `expandJourney()`、`resetJourney()` 和 `playJourney()`；播放模式依次展开身份确认、血糖、症状、人工联系和待办路径。
- [ ] 注册 ECharts `click`、`mouseover`、`mouseout` 事件；tooltip 展示时间、摘要、患者原话和置信度。
- [ ] 提供 HTML 降级线路图，并在 ECharts 初始化成功后隐藏。

### Task 4: 实现原话定位与待办展开

**Files:**

- Modify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`

- [ ] 为完整对话消息添加 `data-node-id`，点击时间点时调用 `focusJourneyNode()`。
- [ ] 在线索详情面板加入“查看患者原话”，切换到完整对话页签并高亮对应消息。
- [ ] 实现 `toggleActionItem(button)`，展开或收起核验清单并同步 `aria-expanded`。
- [ ] 在 `prefers-reduced-motion` 下取消逐段动画，直接显示目标状态。

### Task 5: 浏览器验收

**Files:**

- Verify: `【专项】智能外呼/AI语音随访结果详情页Demo/index.html`

- [ ] 启动静态服务器，使用 Playwright 打开页面并截图。
- [ ] 点击总览卡，确认定位拓扑并选中对应线索。
- [ ] 点击“播放随访路径”“全部展开”“重置”，确认节点数量和详情状态变化。
- [ ] 点击拓扑节点、查看患者原话和待办卡，确认跨区域联动、页签切换和 `aria-expanded`。
- [ ] 运行结构测试与 `git diff --check`，确认无失败和空白错误。

## Self-Review

- 覆盖：患者资料、总览联动、拓扑展开、hover 提示、原话定位、待办清单和无脚本降级均有实现任务。
- 一致性：图节点、正文卡片、对话和待办统一使用 `clueId`；患者资料统一为张翠丽与于磊磊医生。
- 合规：AI 只输出线索、风险提示与待办，不提供诊断或自动修改干预方案。
- 范围：不接真实录音、电话、任务接口或患者数据。
