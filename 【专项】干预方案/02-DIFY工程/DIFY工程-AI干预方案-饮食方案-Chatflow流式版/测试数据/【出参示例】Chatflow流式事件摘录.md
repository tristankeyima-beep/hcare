# Chatflow流式事件摘录

本文件用于记录前端或终端验证时应看到的 SSE 输出顺序示例，不代表完整接口响应。

## 预期顺序

```text
Connected: 200 text/event-stream; charset=utf-8
[event] workflow_started

[node started] 用户输入
[node finished] 用户输入: succeeded

[node started] 流式节点A-健康画像与慢病风险识别
健康画像与慢病风险识别：
正在梳理您的基础健康画像，并结合慢病情况、近期指标、饮食习惯和活动量判断管理重点……
[node finished] 流式节点A-健康画像与慢病风险识别: succeeded

[node started] 流式节点B-管理目标与安全边界校准
管理目标与安全边界校准：
正在校准本次饮食管理的优先级和安全边界，先把血糖、血脂、用药和低血糖风险纳入考虑……
[node finished] 流式节点B-管理目标与安全边界校准: succeeded

[node started] 流式节点C-饮食建议行动化推导
饮食建议行动化推导：
正在把前面的画像和目标校准，转成主食份量、进餐顺序、优质蛋白和控油控盐等可执行动作……
[node finished] 流式节点C-饮食建议行动化推导: succeeded

[node started] 流式节点D-七天餐单执行策略生成
七天餐单执行策略生成：
正在把管理目标转成 7 天饮食执行安排，平衡控糖、控脂、营养搭配和长期坚持难度……
[node finished] 流式节点D-七天餐单执行策略生成: succeeded

[node started] Answer Final
FINAL_PLAN_JSON:
{"planName":"饮食健康处方","planTitle":"个性化饮食管理建议","planSummary":"...","executionPoints":"...","groups":[...]}
[node finished] Answer Final: succeeded

[workflow_finished]
[message_end]
```

## 验收点

- 过程分析内容应早于最终 JSON 输出。
- 过程分析内容只包含自然语言，不包含 schema、代码节点日志、结构化中间 JSON。
- 最终 JSON 应以 `FINAL_PLAN_JSON:` 或前端约定的等价标识开始。
- `FINAL_PLAN_JSON:` 后的内容必须能被解析为合法 JSON。
- 正式展示内容可以包含模型流式生成中的分析过程，体验上应像 AI 健管师在说明自己如何阅读材料、判断重点和做专业取舍。
- 每个阶段播报应控制为短自然段，不应展开成完整问诊报告、长清单或 Markdown 分章节内容。

## 前端处理建议

- 将 `message`、`agent_message`、`text_chunk` 中的文本按顺序追加到过程展示区域。
- 遇到 `FINAL_PLAN_JSON:` 后，将其后的完整文本缓存为最终业务结果，等待流结束后再解析。
- 可将模型流式生成中的分析过程渲染为“分析过程/思考过程”区域；如偶发出现工程痕迹，前端再做过滤兜底。
