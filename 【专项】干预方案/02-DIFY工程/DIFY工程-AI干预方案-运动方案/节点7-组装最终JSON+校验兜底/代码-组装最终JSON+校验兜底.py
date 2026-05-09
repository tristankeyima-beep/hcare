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


def _normalize_text(value, fallback):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalize_group_plan(group_plan):
    parsed = _parse_json(group_plan, {})
    if isinstance(parsed, dict):
        plan = parsed.get("group_plan", [])
    elif isinstance(parsed, list):
        plan = parsed
    else:
        plan = []

    normalized = []
    for item in plan:
        if not isinstance(item, dict):
            continue
        title = _normalize_text(item.get("group_title"), "")
        if not title:
            continue
        normalized.append({
            "group_title": title,
            "group_focus": _normalize_text(item.get("group_focus"), "")
        })
    return normalized


def _normalize_groups(groups):
    parsed = _parse_json(groups, {})
    if isinstance(parsed, dict):
        raw_groups = parsed.get("groups", [])
    elif isinstance(parsed, list):
        raw_groups = parsed
    else:
        raw_groups = []

    normalized = []
    for group in raw_groups:
        if not isinstance(group, dict):
            continue
        title = _normalize_text(group.get("group_title"), "")
        if not title:
            continue

        items = []
        for item in group.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            content = _normalize_text(item.get("content"), "")
            focus_point = _normalize_text(item.get("focus_point"), "")
            if not content:
                continue
            importance = _normalize_text(item.get("importance"), "常规建议")
            if importance not in ALLOWED_IMPORTANCE:
                importance = "常规建议"
            items.append({
                "content": content,
                "focus_point": focus_point or "请结合后续记录和健管师评估进一步调整。",
                "importance": importance
            })

        if items:
            normalized.append({
                "group_title": title,
                "items": items
            })
    return normalized


def _sort_groups_by_plan(groups, group_plan):
    if not group_plan:
        return groups
    order = {item["group_title"]: index for index, item in enumerate(group_plan)}
    return sorted(groups, key=lambda group: order.get(group["group_title"], 999))


def _validate_plan(plan):
    errors = []
    for key in ("plan_name", "plan_title", "plan_summary", "execution_points"):
        if not isinstance(plan.get(key), str) or not plan.get(key).strip():
            errors.append(f"{key} 不能为空")

    groups = plan.get("groups")
    if not isinstance(groups, list) or not groups:
        errors.append("groups 必须是非空数组")
        return errors

    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            errors.append(f"groups[{group_index}] 必须是对象")
            continue
        if not group.get("group_title"):
            errors.append(f"groups[{group_index}].group_title 不能为空")
        items = group.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"groups[{group_index}].items 必须是非空数组")
            continue
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"groups[{group_index}].items[{item_index}] 必须是对象")
                continue
            if not item.get("content"):
                errors.append(f"groups[{group_index}].items[{item_index}].content 不能为空")
            if not item.get("focus_point"):
                errors.append(f"groups[{group_index}].items[{item_index}].focus_point 不能为空")
            if item.get("importance") not in ALLOWED_IMPORTANCE:
                errors.append(f"groups[{group_index}].items[{item_index}].importance 非法")
    return errors


def main(plan_header=None, group_plan=None, groups=None, **kwargs) -> dict:
    header = _parse_json(plan_header, {})
    if not isinstance(header, dict):
        header = {}

    normalized_group_plan = _normalize_group_plan(group_plan)
    normalized_groups = _sort_groups_by_plan(
        _normalize_groups(groups),
        normalized_group_plan
    )

    if not normalized_groups:
        normalized_groups = [{
            "group_title": "运动总原则",
            "items": [{
                "content": "先记录最近一周步数、运动方式、运动时长和运动后的身体反应，再由健管师细化运动方案。",
                "focus_point": "当前可用素材不足，先保证方案可渲染，后续需结合运动记录、指标变化和复诊结果进一步调整。",
                "importance": "重点执行"
            }]
        }]

    final_plan = {
        "plan_name": _normalize_text(header.get("plan_name"), "运动健康处方"),
        "plan_title": _normalize_text(header.get("plan_title"), "个性化运动管理建议"),
        "plan_summary": _normalize_text(
            header.get("plan_summary"),
            "本方案围绕患者当前健康状况和运动管理需求，提供可执行的运动调整建议。"
        ),
        "execution_points": _normalize_text(
            header.get("execution_points"),
            "优先落实重点执行条目；如出现明显不适、连续指标异常或与医生治疗要求冲突，应及时联系医生或健管师。"
        ),
        "groups": normalized_groups
    }

    validation_errors = _validate_plan(final_plan)

    return {
        "final_plan_json": final_plan,
        "final_plan_json_text": json.dumps(final_plan, ensure_ascii=False),
        "validation_errors": validation_errors
    }
