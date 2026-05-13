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


def _get(value, key, default=None):
    if isinstance(value, dict) and key in value:
        return value.get(key)
    return default


def _normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalize_group_plan(value):
    parsed = _parse_json(value, [])
    if isinstance(parsed, dict):
        rawPlan = _get(parsed, "groupPlan", [])
    elif isinstance(parsed, list):
        rawPlan = parsed
    else:
        rawPlan = []

    groupPlan = []
    for item in rawPlan or []:
        if not isinstance(item, dict):
            continue
        title = _normalize_text(_get(item, "groupTitle"))
        if not title:
            continue
        groupPlan.append({
            "groupTitle": title,
            "groupFocus": _normalize_text(_get(item, "groupFocus"))
        })
    return groupPlan


def _normalize_items(rawItems):
    items = []
    for item in rawItems or []:
        if not isinstance(item, dict):
            continue
        content = _normalize_text(_get(item, "content"))
        if not content:
            continue
        importance = _normalize_text(_get(item, "importance"), "常规建议")
        if importance not in ALLOWED_IMPORTANCE:
            importance = "常规建议"
        items.append({
            "itemType": _normalize_text(_get(item, "itemType"), "advice"),
            "day": _get(item, "day", "") or "",
            "title": _normalize_text(_get(item, "title")),
            "content": content,
            "focusPoint": _normalize_text(
                _get(item, "focusPoint"),
                "请结合后续记录和健管师评估进一步调整。"
            ),
            "importance": importance,
            "dailyTotalKcal": _get(item, "dailyTotalKcal", "") or "",
            "dailyTotalProteinG": _get(item, "dailyTotalProteinG", "") or "",
            "dailyTotalFatG": _get(item, "dailyTotalFatG", "") or "",
            "estimatedEnergyDeficitKcal": _get(item, "estimatedEnergyDeficitKcal", "") or "",
            "meals": _get(item, "meals", []) or []
        })
    return items


def _normalize_groups(value):
    parsed = _parse_json(value, [])
    if isinstance(parsed, dict):
        rawGroups = _get(parsed, "groups", [])
    elif isinstance(parsed, list):
        rawGroups = parsed
    else:
        rawGroups = []

    groups = []
    for group in rawGroups or []:
        if not isinstance(group, dict):
            continue
        title = _normalize_text(_get(group, "groupTitle"))
        if not title:
            continue
        items = _normalize_items(_get(group, "items", []))
        if not items:
            continue
        groups.append({
            "groupTitle": title,
            "groupType": _normalize_text(_get(group, "groupType"), "adviceList"),
            "groupSummary": _normalize_text(_get(group, "groupSummary")),
            "displayStyle": _normalize_text(_get(group, "displayStyle"), "list"),
            "dietPlanGoalLabel": _normalize_text(_get(group, "dietPlanGoalLabel")),
            "goalBasis": _normalize_text(_get(group, "goalBasis")),
            "items": items
        })
    return groups


def _sort_and_fill_groups(groups, groupPlan):
    focusByTitle = {
        item["groupTitle"]: item.get("groupFocus", "")
        for item in groupPlan
    }
    order = {
        item["groupTitle"]: index
        for index, item in enumerate(groupPlan)
    }
    for group in groups:
        if not group["groupSummary"]:
            group["groupSummary"] = focusByTitle.get(group["groupTitle"], "")
    return sorted(groups, key=lambda group: order.get(group["groupTitle"], 999))


def main(llmOutput=None, groupPlan=None, groups=None, **kwargs) -> dict:
    parsed = _parse_json(llmOutput, {})
    if not isinstance(parsed, dict):
        parsed = {}

    normalizedGroupPlan = _normalize_group_plan(
        groupPlan if groupPlan not in (None, "") else _get(parsed, "groupPlan", [])
    )
    normalizedGroups = _normalize_groups(
        groups if groups not in (None, "") else _get(parsed, "groups", [])
    )
    normalizedGroups = _sort_and_fill_groups(normalizedGroups, normalizedGroupPlan)

    validationWarnings = []
    if not normalizedGroupPlan:
        validationWarnings.append("groupPlan 为空或不可解析")
    if not normalizedGroups:
        validationWarnings.append("groups 为空或无有效 items")

    return {
        "groupPlan": normalizedGroupPlan,
        "groupPlanText": json.dumps({"groupPlan": normalizedGroupPlan}, ensure_ascii=False),
        "groups": normalizedGroups,
        "groupsText": json.dumps({"groups": normalizedGroups}, ensure_ascii=False),
        "groupPlanCount": len(normalizedGroupPlan),
        "groupsCount": len(normalizedGroups),
        "validationWarnings": validationWarnings,
        "validationWarningsCount": len(validationWarnings)
    }
