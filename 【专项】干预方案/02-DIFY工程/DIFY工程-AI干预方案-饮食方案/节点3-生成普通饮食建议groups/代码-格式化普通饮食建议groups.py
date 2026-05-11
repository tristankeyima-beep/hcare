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


def _normalize_importance(value, warnings, group_title, item_index):
    importance = _normalize_text(value, "常规建议")
    if importance not in ALLOWED_IMPORTANCE:
        warnings.append(f"{group_title}.items[{item_index}].importance 非法，已归一为 常规建议。")
        return "常规建议"
    return importance


def _normalize_item(item, warnings, group_title, item_index):
    if not isinstance(item, dict):
        warnings.append(f"{group_title}.items[{item_index}] 不是对象，已跳过。")
        return None

    content = _normalize_text(item.get("content"), "")
    if not content:
        warnings.append(f"{group_title}.items[{item_index}].content 为空，已跳过。")
        return None

    output = {
        key: value
        for key, value in item.items()
        if key not in ("item_type", "title", "content", "focus_point", "importance")
    }
    output.update({
        "item_type": "advice",
        "title": _normalize_text(item.get("title"), "饮食建议"),
        "content": content,
        "focus_point": _normalize_text(item.get("focus_point"), "请结合后续记录和健管师评估进一步调整。"),
        "importance": _normalize_importance(item.get("importance"), warnings, group_title, item_index),
    })
    return output


def _normalize_group(group, warnings, group_index):
    if not isinstance(group, dict):
        warnings.append(f"groups[{group_index}] 不是对象，已跳过。")
        return None

    group_title = _normalize_text(group.get("group_title"), "")
    if not group_title:
        warnings.append(f"groups[{group_index}].group_title 为空，已跳过。")
        return None

    if group.get("group_type") == "weekly_meal_plan":
        warnings.append(f"{group_title} 为 weekly_meal_plan，已跳过；7天菜谱应由节点4生成。")
        return None

    output = {
        key: value
        for key, value in group.items()
        if key not in ("group_title", "group_type", "group_summary", "display_style", "items")
    }
    output.update({
        "group_title": group_title,
        "group_type": "advice_list",
        "group_summary": _normalize_text(group.get("group_summary"), ""),
        "display_style": _normalize_text(group.get("display_style"), "list"),
    })

    items = []
    for item_index, item in enumerate(group.get("items", []) or []):
        normalized = _normalize_item(item, warnings, group_title, item_index)
        if normalized:
            items.append(normalized)
    if not items:
        warnings.append(f"{group_title}.items 为空或无有效建议，已跳过该 group。")
        return None

    output["items"] = items
    return output


def _normalize_groups(value):
    warnings = []
    groups = []
    raw_groups = _extract_groups(value)
    for group_index, group in enumerate(raw_groups):
        normalized = _normalize_group(group, warnings, group_index)
        if normalized:
            groups.append(normalized)
    if not groups:
        warnings.append("未解析到有效普通饮食建议 groups。")
    return groups, warnings


def main(groups=None, text=None, llm_text=None, llm_output=None, **kwargs) -> dict:
    source = _first_groups_source(groups, text, llm_text, llm_output, kwargs)
    formatted_groups, warnings = _normalize_groups(source)
    item_count = sum(len(group.get("items", [])) for group in formatted_groups)
    return {
        "groups": _json_text(formatted_groups),
        "formatted_groups_json": _json_text({"groups": formatted_groups}),
        "groups_count": len(formatted_groups),
        "items_count": item_count,
        "format_warnings": _json_text(warnings),
    }
