import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}


def _parse_json(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(stripped[start:end + 1])
                except json.JSONDecodeError:
                    return default
    return default


def _text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalize_item(item):
    if not isinstance(item, dict):
        return None
    content = _text(item.get("content"))
    if not content:
        return None
    importance = _text(item.get("importance"), "常规建议")
    if importance not in ALLOWED_IMPORTANCE:
        importance = "常规建议"
    return {
        "itemType": "advice",
        "day": item.get("day") or "",
        "title": _text(item.get("title")),
        "content": content,
        "focusPoint": _text(item.get("focusPoint"), "请结合复诊结果和健管师评估进一步调整。"),
        "importance": importance,
        "dailyTotalKcal": item.get("dailyTotalKcal") or "",
        "dailyTotalProteinG": item.get("dailyTotalProteinG") or "",
        "dailyTotalFatG": item.get("dailyTotalFatG") or "",
        "estimatedEnergyDeficitKcal": item.get("estimatedEnergyDeficitKcal") or "",
        "meals": item.get("meals") if isinstance(item.get("meals"), list) else [],
    }


def main(llmText=None, text=None, **kwargs) -> dict:
    parsed = _parse_json(llmText if llmText is not None else text, {})
    if not isinstance(parsed, dict):
        parsed = {}

    group_plan = []
    for item in parsed.get("groupPlan", []) or []:
        if not isinstance(item, dict):
            continue
        title = _text(item.get("groupTitle"))
        if title:
            group_plan.append({"groupTitle": title, "groupFocus": _text(item.get("groupFocus"))})

    groups = []
    for group in parsed.get("groups", []) or []:
        if not isinstance(group, dict):
            continue
        title = _text(group.get("groupTitle"))
        if not title:
            continue
        items = [_normalize_item(item) for item in group.get("items", []) or []]
        items = [item for item in items if item]
        if not items:
            continue
        groups.append({
            "groupTitle": title,
            "groupType": "adviceList",
            "groupSummary": _text(group.get("groupSummary"), _text(group.get("groupFocus"))),
            "displayStyle": "list",
            "dietPlanGoalLabel": _text(group.get("dietPlanGoalLabel")),
            "goalBasis": _text(group.get("goalBasis")),
            "items": items,
        })

    return {
        "groupPlan": json.dumps({"groupPlan": group_plan}, ensure_ascii=False),
        "groups": json.dumps({"groups": groups}, ensure_ascii=False),
        "groupsCount": len(groups),
    }
