export const nodeTypeIcons = {
  start: {
    label: "接收信息",
    color: "#16A34A",
    background: "#DCFCE7",
    icon: "start.svg",
  },
  "if-else": {
    label: "条件判断",
    color: "#D97706",
    background: "#FEF3C7",
    icon: "if-else.svg",
  },
  code: {
    label: "整理数据",
    color: "#2563EB",
    background: "#DBEAFE",
    icon: "code.svg",
  },
  llm: {
    label: "智能分析",
    color: "#7C3AED",
    background: "#EDE9FE",
    icon: "llm.svg",
  },
  answer: {
    label: "生成结果",
    color: "#0891B2",
    background: "#CFFAFE",
    icon: "answer.svg",
  },
};

export function getNodeTypeIcon(nodeType) {
  return nodeTypeIcons[nodeType] || {
    label: "流程节点",
    color: "#64748B",
    background: "#F1F5F9",
    icon: null,
  };
}
