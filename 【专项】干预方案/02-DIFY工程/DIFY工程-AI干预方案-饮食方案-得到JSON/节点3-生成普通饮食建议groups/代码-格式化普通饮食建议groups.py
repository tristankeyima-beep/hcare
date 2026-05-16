import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}


def _json_text(value):
    return json.dumps(value, ensure_ascii=False)


def _normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _parse_json(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    return default
    return default


def _first_groups_source(*values):
    for value in values:
        parsed = _parse_json(value, None)
        if parsed is None:
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            nested = _parse_json(parsed.get("text"), None)
            if nested is not None:
                return nested
        return parsed
    return {}


def _extract_groups(value):
    parsed = _parse_json(value, {})
    if isinstance(parsed, dict):
        groups = parsed.get("groups", [])
    elif isinstance(parsed, list):
        groups = parsed
    else:
        groups = []
    return groups if isinstance(groups, list) else []


def _normalize_importance(value, warnings, groupTitle, itemIndex):
    importance = _normalize_text(value, "常规建议")
    if importance not in ALLOWED_IMPORTANCE:
        warnings.append(f"{groupTitle}.items[{itemIndex}].importance 非法，已归一为 常规建议。")
        return "常规建议"
    return importance


def _normalize_item(item, warnings, groupTitle, itemIndex):
    if not isinstance(item, dict):
        warnings.append(f"{groupTitle}.items[{itemIndex}] 不是对象，已跳过。")
        return None

    content = _normalize_text(item.get("content"), "")
    if not content:
        warnings.append(f"{groupTitle}.items[{itemIndex}].content 为空，已跳过。")
        return None

    output = {
        key: value
        for key, value in item.items()
        if key not in ("itemType", "title", "content", "focusPoint", "importance")
    }
    output.update({
        "itemType": "advice",
        "title": _normalize_text(item.get("title"), "饮食建议"),
        "content": content,
        "focusPoint": _normalize_text(item.get("focusPoint"), "请结合后续记录和健管师评估进一步调整。"),
        "importance": _normalize_importance(item.get("importance"), warnings, groupTitle, itemIndex),
    })
    return output


def _normalize_group(group, warnings, groupIndex):
    if not isinstance(group, dict):
        warnings.append(f"groups[{groupIndex}] 不是对象，已跳过。")
        return None

    groupTitle = _normalize_text(group.get("groupTitle"), "")
    if not groupTitle:
        warnings.append(f"groups[{groupIndex}].groupTitle 为空，已跳过。")
        return None

    if group.get("groupType") == "weeklyMealPlan":
        warnings.append(f"{groupTitle} 为 weeklyMealPlan，已跳过；7天菜谱应由节点4生成。")
        return None

    output = {
        key: value
        for key, value in group.items()
        if key not in ("groupTitle", "groupType", "groupSummary", "displayStyle", "items")
    }
    output.update({
        "groupTitle": groupTitle,
        "groupType": "adviceList",
        "groupSummary": _normalize_text(group.get("groupSummary"), ""),
        "displayStyle": _normalize_text(group.get("displayStyle"), "list"),
    })

    items = []
    for itemIndex, item in enumerate(group.get("items", []) or []):
        normalized = _normalize_item(item, warnings, groupTitle, itemIndex)
        if normalized:
            items.append(normalized)
    if not items:
        warnings.append(f"{groupTitle}.items 为空或无有效建议，已跳过该 group。")
        return None

    output["items"] = items
    return output


def _normalize_groups(value):
    warnings = []
    groups = []
    rawGroups = _extract_groups(value)
    for groupIndex, group in enumerate(rawGroups):
        normalized = _normalize_group(group, warnings, groupIndex)
        if normalized:
            groups.append(normalized)
    if not groups:
        warnings.append("未解析到有效普通饮食建议 groups。")
    return groups, warnings


def main(groups=None, text=None, llmText=None, llmOutput=None, **kwargs) -> dict:
    source = _first_groups_source(groups, text, llmText, llmOutput, kwargs)
    formattedGroups, warnings = _normalize_groups(source)
    itemCount = sum(len(group.get("items", [])) for group in formattedGroups)
    return {
        "groups": _json_text(formattedGroups),
        "formattedGroupsJson": _json_text({"groups": formattedGroups}),
        "groupsCount": len(formattedGroups),
        "itemsCount": itemCount,
        "formatWarnings": _json_text(warnings),
    }
