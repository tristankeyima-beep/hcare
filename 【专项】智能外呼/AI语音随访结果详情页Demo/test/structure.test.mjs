import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");

test("患者与管理医生资料按指定案例展示", () => {
  const required = [
    "张翠丽",
    "女 / 61 岁 / 1964-09-12",
    "于磊磊",
    "糖尿病代谢病科\\(泰安市中心医院\\)",
  ];
  for (const value of required) assert.match(html, new RegExp(value));
  assert.doesNotMatch(html, /王淑华/);
});

test("页面具备线索拓扑和真实操作顺序联动", () => {
  const required = [
    "followup-journey-chart",
    "journey-fallback",
    "data-focus-node",
    "playJourney",
    "expandJourney",
    "resetJourney",
    "focusJourneyNode",
    "toggleActionItem",
    "查看患者原话",
    "aria-expanded=\"false\"",
    "echarts@5.6.0",
    "gsap@3.13.0",
  ];
  for (const value of required) assert.match(html, new RegExp(value));
});

test("正式展示版保留风险、证据与人工核验边界", () => {
  const required = [
    "本人接听 · 已完成",
    "12.6 mmol/L",
    "疑似低血糖症状",
    "患者主动要求人工联系",
    "需健管师核验",
    "通话详情",
    "完整对话",
    "AI 抽取依据",
    "switchEvidenceTab",
    "role=\"tabpanel\"",
  ];
  const forbidden = ["自动调整处方", "自动修改干预方案", "社区卫生服务中心"];

  for (const value of required) assert.match(html, new RegExp(value));
  for (const value of forbidden) assert.doesNotMatch(html, new RegExp(value));
});

test("页面展示阿里云 JobGroup、Job 与两次 Task 执行链路", () => {
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

test("页面明确区分原始数据与 AI 生成内容", () => {
  assert.match(html, /基于原始通话数据生成，待健管师核验/);
  assert.ok((html.match(/class="ai-badge"/g) || []).length >= 6);
});
