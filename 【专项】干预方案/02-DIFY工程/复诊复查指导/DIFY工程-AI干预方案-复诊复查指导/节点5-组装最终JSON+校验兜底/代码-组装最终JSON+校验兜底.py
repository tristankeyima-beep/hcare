import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}
GROUP_FIELDS = (
    "groupTitle",
    "groupType",
    "groupSummary",
    "displayStyle",
    "dietPlanGoalLabel",
    "goalBasis",
    "items",
)
ITEM_FIELDS = (
    "itemType",
    "day",
    "title",
    "content",
    "focusPoint",
    "importance",
    "dailyTotalKcal",
    "dailyTotalProteinG",
    "dailyTotalFatG",
    "estimatedEnergyDeficitKcal",
    "meals",
)


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
    if not isinstance(value, dict):
        return default
    return value.get(key, default)


def _normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalize_group_plan(groupPlan):
    parsed = _parse_json(groupPlan, {})
    if isinstance(parsed, dict):
        plan = _get(parsed, "groupPlan", [])
    elif isinstance(parsed, list):
        plan = parsed
    else:
        plan = []

    normalized = []
    for item in plan:
        if not isinstance(item, dict):
            continue
        title = _normalize_text(_get(item, "groupTitle"))
        if title:
            normalized.append({
                "groupTitle": title,
                "groupFocus": _normalize_text(_get(item, "groupFocus")),
            })
    return normalized


def _normalize_items(raw_items, keep_empty=False):
    normalized = []
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        content = _normalize_text(_get(item, "content"))
        focusPoint = _normalize_text(_get(item, "focusPoint"))
        if not content and not keep_empty:
            continue
        importance = _normalize_text(_get(item, "importance"), "常规建议")
        if importance not in ALLOWED_IMPORTANCE:
            importance = "常规建议"
        normalized.append({
            "itemType": _normalize_text(_get(item, "itemType"), "advice"),
            "day": _get(item, "day", "") or "",
            "title": _normalize_text(_get(item, "title")),
            "content": content,
            "focusPoint": focusPoint,
            "importance": importance,
            "dailyTotalKcal": _get(item, "dailyTotalKcal", "") or "",
            "dailyTotalProteinG": _get(item, "dailyTotalProteinG", "") or "",
            "dailyTotalFatG": _get(item, "dailyTotalFatG", "") or "",
            "estimatedEnergyDeficitKcal": _get(item, "estimatedEnergyDeficitKcal", "") or "",
            "meals": _get(item, "meals", default=[]) if isinstance(_get(item, "meals", default=[]), list) else [],
        })
    return normalized


def _normalize_groups(groups):
    parsed = _parse_json(groups, {})
    if isinstance(parsed, dict):
        raw_groups = _get(parsed, "groups", default=[])
    elif isinstance(parsed, list):
        raw_groups = parsed
    else:
        raw_groups = []

    normalized = []
    for group in raw_groups:
        if not isinstance(group, dict):
            continue
        title = _normalize_text(_get(group, "groupTitle"))
        if not title:
            continue
        items = _normalize_items(_get(group, "items", default=[]), keep_empty=True)
        normalized.append({
            "groupTitle": title,
            "groupType": _normalize_text(_get(group, "groupType"), "adviceList"),
            "groupSummary": _normalize_text(_get(group, "groupSummary"), _normalize_text(_get(group, "groupFocus"))),
            "displayStyle": _normalize_text(_get(group, "displayStyle"), "list"),
            "dietPlanGoalLabel": _normalize_text(_get(group, "dietPlanGoalLabel")),
            "goalBasis": _normalize_text(_get(group, "goalBasis")),
            "items": items,
        })
    return normalized


def _sort_groups_by_plan(groups, groupPlan):
    if not groupPlan:
        return groups
    order = {item["groupTitle"]: index for index, item in enumerate(groupPlan)}
    return sorted(groups, key=lambda group: order.get(group["groupTitle"], 999))


def _fill_group_summary(groups, groupPlan):
    focusByTitle = {item["groupTitle"]: item.get("groupFocus", "") for item in groupPlan}
    for group in groups:
        if not group.get("groupSummary"):
            group["groupSummary"] = focusByTitle.get(group.get("groupTitle"), "")
    return groups


def _align_object_fields(obj, fields):
    return {field: obj.get(field, [] if field == "meals" else "") for field in fields}


def _align_output_fields(plan):
    aligned_groups = []
    for group in plan.get("groups", []) or []:
        group = dict(group)
        group["items"] = [
            _align_object_fields(item, ITEM_FIELDS) if isinstance(item, dict) else item
            for item in group.get("items", []) or []
        ]
        aligned_groups.append(_align_object_fields(group, GROUP_FIELDS))
    plan["groups"] = aligned_groups
    return plan


def _validate_plan(plan):
    errors = []
    for key in ("planName", "planTitle", "planSummary", "executionPoints"):
        if not isinstance(plan.get(key), str) or not plan.get(key).strip():
            errors.append(f"{key} 不能为空")

    groups = plan.get("groups")
    if not isinstance(groups, list) or not groups:
        errors.append("groups 必须是非空数组")
        return errors

    for groupIndex, group in enumerate(groups):
        if not isinstance(group, dict):
            errors.append(f"groups[{groupIndex}] 必须是对象")
            continue
        for key in ("groupTitle", "groupType", "displayStyle"):
            if not group.get(key):
                errors.append(f"groups[{groupIndex}].{key} 不能为空")
        items = group.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"groups[{groupIndex}].items 必须是非空数组")
            continue
        for itemIndex, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"groups[{groupIndex}].items[{itemIndex}] 必须是对象")
                continue
            if not item.get("content"):
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].content 不能为空")
            if not item.get("focusPoint"):
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].focusPoint 不能为空")
            if item.get("importance") not in ALLOWED_IMPORTANCE:
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].importance 非法")
    return errors


def _fallback_groups():
    return [{
        "groupTitle": "复诊复查总原则",
        "groupType": "adviceList",
        "groupSummary": "当前可用素材不足，先输出最小可执行复诊复查建议。",
        "displayStyle": "list",
        "dietPlanGoalLabel": "",
        "goalBasis": "",
        "items": [{
            "itemType": "advice",
            "day": "",
            "title": "先补齐近期复查资料",
            "content": "先整理最近一次随访、居家监测、用药和检查结果，再由医生或健管师细化复诊复查安排。",
            "focusPoint": "当前可用素材不足，先保证方案可渲染，后续需结合复诊结果和指标变化进一步调整。",
            "importance": "重点执行",
            "dailyTotalKcal": "",
            "dailyTotalProteinG": "",
            "dailyTotalFatG": "",
            "estimatedEnergyDeficitKcal": "",
            "meals": [],
        }],
    }]


def main(planHeader=None, groupPlan=None, groups=None, **kwargs) -> dict:
    header = _parse_json(planHeader, {})
    if not isinstance(header, dict):
        header = {}

    normalizedGroupPlan = _normalize_group_plan(groupPlan)
    normalizedGroups = _sort_groups_by_plan(_normalize_groups(groups), normalizedGroupPlan)
    normalizedGroups = _fill_group_summary(normalizedGroups, normalizedGroupPlan)

    if not normalizedGroups:
        normalizedGroups = _fallback_groups()

    finalPlan = {
        "planName": _normalize_text(_get(header, "planName"), "复诊复查指导"),
        "planTitle": _normalize_text(_get(header, "planTitle"), "个性化复诊复查安排"),
        "planSummary": _normalize_text(
            _get(header, "planSummary"),
            "本方案围绕患者当前健康状况和复诊复查需求，提供可执行的复诊复查安排。",
        ),
        "executionPoints": _normalize_text(
            _get(header, "executionPoints"),
            "优先完成重点复查项目；复查结果及时回传给医生或健管师；如出现连续指标异常、明显不适或用药中断，应提前联系医生或健管师。",
        ),
        "groups": normalizedGroups,
    }
    finalPlan = _align_output_fields(finalPlan)
    validationErrors = _validate_plan(finalPlan)

    return {
        "finalPlanJson": finalPlan,
        "finalPlanJsonText": json.dumps(finalPlan, ensure_ascii=False),
        "validationErrors": validationErrors,
        "validationErrorsCount": len(validationErrors),
        "groupsCount": len(normalizedGroups),
    }
