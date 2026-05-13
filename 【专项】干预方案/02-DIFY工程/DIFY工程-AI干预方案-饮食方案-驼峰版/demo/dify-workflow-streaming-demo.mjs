#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_API_BASE = "https://dify.hzmarvel.com/v1";
const DEFAULT_INPUT_FILE = "../测试数据/【入参】饮食方案工作流测试入参.json";

const apiBase = (process.env.DIFY_API_BASE || DEFAULT_API_BASE).replace(/\/+$/, "");
const apiKey = process.env.DIFY_API_KEY;
const demoDir = dirname(fileURLToPath(import.meta.url));
const inputFile = resolve(demoDir, process.argv[2] || DEFAULT_INPUT_FILE);
const user = process.env.DIFY_USER || "workflow-streaming-demo";
const showTextChunks = process.env.DIFY_SHOW_TEXT_CHUNKS === "1";

if (!apiKey) {
  console.error("Missing DIFY_API_KEY. Example: DIFY_API_KEY='app-***' node demo/dify-workflow-streaming-demo.mjs");
  process.exit(1);
}

const rawInputs = JSON.parse(await readFile(inputFile, "utf8"));
const inputs = stringifyParagraphInputs(rawInputs);

const response = await fetch(`${apiBase}/workflows/run`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    inputs,
    response_mode: "streaming",
    user,
  }),
});

if (!response.ok || !response.body) {
  const text = await response.text();
  throw new Error(`Dify request failed: ${response.status} ${response.statusText}\n${text}`);
}

console.log(`Connected: ${response.status} ${response.headers.get("content-type")}`);

let buffer = "";
let finalOutputs = null;
const decoder = new TextDecoder();

for await (const chunk of response.body) {
  buffer += decoder.decode(chunk, { stream: true });
  const events = buffer.split("\n\n");
  buffer = events.pop() || "";

  for (const eventBlock of events) {
    const event = parseSseEvent(eventBlock);
    if (!event) continue;

    if (event.type === "ping") {
      console.log("[ping]");
      continue;
    }

    if (event.payload.event === "node_started") {
      console.log(`[node started] ${event.payload.data?.title || event.payload.data?.node_type || "unknown"}`);
      continue;
    }

    if (event.payload.event === "node_finished") {
      const data = event.payload.data || {};
      console.log(`[node finished] ${data.title || data.node_type || "unknown"}: ${data.status || "unknown"}`);
      continue;
    }

    if (event.payload.event === "workflow_finished") {
      finalOutputs = event.payload.data?.outputs || null;
      console.log("[workflow finished]");
      continue;
    }

    if (event.payload.event === "text_chunk") {
      const chunkText = event.payload.data?.text || event.payload.data?.answer || "";
      if (showTextChunks && chunkText) {
        process.stdout.write(chunkText);
      } else {
        console.log(`[text_chunk] ${chunkText.length} chars`);
      }
      continue;
    }

    console.log(`[event] ${event.payload.event}`);
  }
}

if (!finalOutputs) {
  throw new Error("Workflow stream ended without workflow_finished outputs.");
}

const finalPlanJsonText = finalOutputs.finalPlanJsonText;
if (typeof finalPlanJsonText === "string" && finalPlanJsonText.trim()) {
  const finalPlan = JSON.parse(finalPlanJsonText);
  console.log("\nFinal plan preview:");
  console.log(JSON.stringify({
    planName: finalPlan.planName,
    planTitle: finalPlan.planTitle,
    groupsCount: Array.isArray(finalPlan.groups) ? finalPlan.groups.length : 0,
  }, null, 2));
} else {
  console.log("\nFinal outputs:");
  console.log(JSON.stringify(finalOutputs, null, 2));
}

function stringifyParagraphInputs(value) {
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      typeof item === "string" ? item : JSON.stringify(item),
    ]),
  );
}

function parseSseEvent(block) {
  const lines = block.split("\n").filter(Boolean);
  const eventType = lines
    .find((line) => line.startsWith("event:"))
    ?.slice("event:".length)
    .trim();
  const dataLines = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim());

  if (eventType && dataLines.length === 0) {
    return { type: eventType, payload: null };
  }

  if (dataLines.length === 0) return null;

  return {
    type: eventType || "message",
    payload: JSON.parse(dataLines.join("\n")),
  };
}
