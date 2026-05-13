# Node Type Icons

这组图标用于 Chatflow 运行过程展示，按 Dify `node_type` 做语义区分。

| node_type | 展示名称 | 主题色 | 文件 |
| --- | --- | --- | --- |
| `start` | 接收信息 | `#16A34A` | `start.svg` |
| `if-else` | 条件判断 | `#D97706` | `if-else.svg` |
| `code` | 整理数据 | `#2563EB` | `code.svg` |
| `llm` | 智能分析 | `#7C3AED` | `llm.svg` |
| `answer` | 生成结果 | `#0891B2` | `answer.svg` |

设计规则：

- 统一使用 24x24 SVG，适合节点时间线、列表、卡片标题和运行状态栏。
- 每个图标由浅色底圆和主题色线性符号组成，便于在浅色界面中快速识别。
- 前端可以直接引用 SVG 文件，也可以使用 `node-type-icons.js` 作为展示映射。

示例：

```js
import { getNodeTypeIcon } from "./node-type-icons.js";

const meta = getNodeTypeIcon("llm");
// { label: "智能分析", color: "#7C3AED", background: "#EDE9FE", icon: "llm.svg" }
```
