# Dify Streaming Demos

These demos call Dify APIs with `response_mode: "streaming"` and parse the returned SSE stream.

## Workflow Demo

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-饮食方案-得到JSON"
DIFY_API_KEY="app-***" node demo/dify-workflow-streaming-demo.mjs
```

Optional environment variables:

- `DIFY_API_BASE`: defaults to `https://dify.hzmarvel.com/v1`
- `DIFY_USER`: defaults to `workflow-streaming-demo`
- `DIFY_SHOW_TEXT_CHUNKS=1`: print `text_chunk` content instead of only showing its length

Show text chunks:

```bash
DIFY_API_KEY="app-***" DIFY_SHOW_TEXT_CHUNKS=1 node demo/dify-workflow-streaming-demo.mjs
```

Optional input file:

```bash
DIFY_API_KEY="app-***" node demo/dify-workflow-streaming-demo.mjs ./测试数据/【入参】饮食方案工作流测试入参.json
```

## Chatflow Demo

```bash
cd "/Users/Tristan/TristansDevelop/TristanProject/AIHcare/【专项】干预方案/02-DIFY工程/DIFY工程-AI干预方案-饮食方案-得到JSON"
DIFY_API_KEY="app-***" node demo/dify-chatflow-streaming-demo.mjs
```

Optional environment variables:

- `DIFY_API_BASE`: defaults to `https://dify.hzmarvel.com/v1`
- `DIFY_USER`: defaults to `chatflow-streaming-demo`
- `DIFY_PLAN_TYPE`: defaults to `diet`
- `DIFY_QUERY`: defaults to `请根据基础档案生成饮食方案。`
- `DIFY_CONVERSATION_ID`: defaults to an empty conversation
- `DIFY_INSPECT_NODE_TITLE`: print outputs for the matching `node_finished` event
- `DIFY_PRINT_NODE_OUTPUTS=1`: print full inspected node outputs instead of previews

Inspect a node's internal outputs:

```bash
DIFY_API_KEY="app-***" DIFY_INSPECT_NODE_TITLE="将LLM生成的饮食画像结构化" node demo/dify-chatflow-streaming-demo.mjs
```

Print full internal outputs:

```bash
DIFY_API_KEY="app-***" DIFY_INSPECT_NODE_TITLE="将LLM生成的饮食画像结构化" DIFY_PRINT_NODE_OUTPUTS=1 node demo/dify-chatflow-streaming-demo.mjs
```

Optional source file:

```bash
DIFY_API_KEY="app-***" node demo/dify-chatflow-streaming-demo.mjs ./my-basic-profile.json
```

If the source file contains `inputs`, the demo uses `inputs`. Otherwise it stringifies all top-level fields and sends them as Dify inputs.

## Notes

- Dify `paragraph` variables must be strings. The demo converts object and array inputs to JSON strings before sending them.
- The stream emits workflow and node lifecycle events. For this workflow, the final answer is read from `workflow_finished.data.outputs.finalPlanJsonText`.
- The Chatflow demo calls `/chat-messages` and prints streamed answer chunks directly.
