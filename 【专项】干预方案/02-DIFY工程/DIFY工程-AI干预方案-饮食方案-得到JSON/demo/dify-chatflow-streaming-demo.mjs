#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_API_BASE = "https://dify.hzmarvel.com/v1";
const DEFAULT_SOURCE_FILE = "../测试数据/【入参】饮食方案工作流测试入参.json";
const DEFAULT_QUERY = "请根据基础档案生成饮食方案。";

const apiBase = (process.env.DIFY_API_BASE || DEFAULT_API_BASE).replace(/\/+$/, "");
const apiKey = process.env.DIFY_API_KEY;
const demoDir = dirname(fileURLToPath(import.meta.url));
const sourceFile = resolve(demoDir, process.argv[2] || DEFAULT_SOURCE_FILE);
const user = process.env.DIFY_USER || "chatflow-streaming-demo";
const query = process.env.DIFY_QUERY || DEFAULT_QUERY;
const planType = process.env.DIFY_PLAN_TYPE || "diet";
const inspectNodeTitle = process.env.DIFY_INSPECT_NODE_TITLE || "";
const printInspectedNodeOutputs = process.env.DIFY_PRINT_NODE_OUTPUTS === "1";

if (!apiKey) {
  console.error("Missing DIFY_API_KEY. Example: DIFY_API_KEY='app-***' node demo/dify-chatflow-streaming-demo.mjs");
  process.exit(1);
}

const source = JSON.parse(await readFile(sourceFile, "utf8"));
const inputs = buildInputs(source);

const response = await fetch(`${apiBase}/chat-messages`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    inputs,
    query,
    response_mode: "streaming",
    conversation_id: process.env.DIFY_CONVERSATION_ID || "",
    user,
  }),
});

if (!response.ok || !response.body) {
  const text = await response.text();
  throw new Error(`Dify request failed: ${response.status} ${response.statusText}\n${text}`);
}

console.log(`Connected: ${response.status} ${response.headers.get("content-type")}`);
console.log("Streaming answer:\n");

let buffer = "";
let answer = "";
let finalMetadata = null;
const nodeTimings = [];
const decoder = new TextDecoder();

for await (const chunk of response.body) {
  buffer += decoder.decode(chunk, { stream: true });
  const events = buffer.split("\n\n");
  buffer = events.pop() || "";

  for (const eventBlock of events) {
    const event = parseSseEvent(eventBlock);
    if (!event) continue;

    if (event.type === "ping") {
      process.stdout.write(".");
      continue;
    }

    const payload = event.payload;
    const eventName = payload.event;

    if (eventName === "message" || eventName === "agent_message" || eventName === "text_chunk") {
      const text = payload.answer || payload.data?.text || "";
      if (text) {
        answer += text;
        process.stdout.write(text);
      }
      continue;
    }

    if (eventName === "node_started") {
      process.stdout.write(`\n\n[node started] ${payload.data?.title || payload.data?.node_type || "unknown"}\n`);
      continue;
    }

    if (eventName === "node_finished") {
      const data = payload.data || {};
      const elapsed = typeof data.elapsed_time === "number" ? data.elapsed_time : null;
      nodeTimings.push({
        title: data.title || data.node_type || "unknown",
        type: data.node_type || "",
        status: data.status || "unknown",
        elapsedSeconds: elapsed,
      });
      process.stdout.write(`\n[node finished] ${data.title || data.node_type || "unknown"}: ${data.status || "unknown"}${elapsed === null ? "" : ` (${elapsed.toFixed(3)}s)`}\n`);
      if (inspectNodeTitle && data.title === inspectNodeTitle) {
        printNodeOutputs(data.outputs || {});
      }
      continue;
    }

    if (eventName === "message_end") {
      finalMetadata = payload.metadata || null;
      process.stdout.write("\n\n[message_end]\n");
      continue;
    }

    if (eventName === "workflow_finished") {
      process.stdout.write("\n[workflow_finished]\n");
      continue;
    }

    process.stdout.write(`\n[event] ${eventName}\n`);
  }
}

console.log("\nSummary:");
console.log(JSON.stringify({
  answerChars: answer.length,
  totalTokens: finalMetadata?.usage?.total_tokens,
  totalPrice: finalMetadata?.usage?.total_price,
  currency: finalMetadata?.usage?.currency,
  nodeTimings,
}, null, 2));

function buildInputs(source) {
  const rawInputs = source.inputs && typeof source.inputs === "object" ? source.inputs : source;
  return Object.fromEntries(
    Object.entries({ ...rawInputs, planType: rawInputs.planType || planType }).map(([key, value]) => [
      key,
      typeof value === "string" ? value : JSON.stringify(value),
    ]),
  );
}

function printNodeOutputs(outputs) {
  const outputKeys = Object.keys(outputs);
  process.stdout.write(`[inspect node outputs] keys: ${outputKeys.join(", ")}\n`);

  if (printInspectedNodeOutputs) {
    process.stdout.write(`${JSON.stringify(outputs, null, 2)}\n`);
    return;
  }

  for (const [key, value] of Object.entries(outputs)) {
    const text = typeof value === "string" ? value : JSON.stringify(value);
    const preview = text.length > 120 ? `${text.slice(0, 120)}...` : text;
    process.stdout.write(`[inspect node outputs] ${key}: ${preview} (${text.length} chars)\n`);
  }
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
