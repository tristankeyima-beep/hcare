import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}
REQUIRED_MEALS = {"早餐", "午餐", "晚餐"}
FOOD_NUMBER_FIELDS = ("amount_g", "kcal", "protein_g", "fat_g")


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
        group_output = {
            key: value
            for key, value in group.items()
            if key not in ("items", "group_title", "group_type", "group_summary", "display_style")
        }
        group_output.update({
            "group_title": title,
            "group_type": _normalize_text(group.get("group_type"), "advice_list"),
            "group_summary": _normalize_text(group.get("group_summary"), ""),
            "display_style": _normalize_text(group.get("display_style"), "list")
        })

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
            item_output = {
                key: value
                for key, value in item.items()
                if key not in ("item_type", "content", "focus_point", "importance")
            }
            item_output.update({
                "item_type": _normalize_text(item.get("item_type"), "advice"),
                "content": content,
                "focus_point": focus_point or "请结合后续记录和健管师评估进一步调整。",
                "importance": importance
            })
            items.append(item_output)

        if items:
            group_output["items"] = items
            normalized.append(group_output)
    return normalized


def _normalize_meal_plan_group(meal_plan_group):
    parsed = _parse_json(meal_plan_group, {})
    if isinstance(parsed, dict) and "meal_plan_group" in parsed:
        parsed = parsed.get("meal_plan_group")
    if not isinstance(parsed, dict):
        return None

    group = {
        key: value
        for key, value in parsed.items()
        if key not in ("group_title", "group_type", "group_summary", "display_style", "items", "diet_plan_goal")
    }
    group.update({
        "group_title": _normalize_text(parsed.get("group_title"), "最近7天饮食执行菜谱"),
        "group_type": "weekly_meal_plan",
        "group_summary": _normalize_text(parsed.get("group_summary"), ""),
        "display_style": _normalize_text(parsed.get("display_style"), "weekly_meal_plan")
    })

    items = []
    for raw_item in parsed.get("items", []) or []:
        if not isinstance(raw_item, dict):
            continue
        content = _normalize_text(raw_item.get("content"), "")
        if not content:
            continue
        importance = _normalize_text(raw_item.get("importance"), "重点执行")
        if importance not in ALLOWED_IMPORTANCE:
            importance = "重点执行"
        item = {
            key: value
            for key, value in raw_item.items()
            if key not in ("item_type", "content", "focus_point", "importance")
        }
        item.update({
            "item_type": "daily_meal_plan",
            "content": content,
            "focus_point": _normalize_text(raw_item.get("focus_point"), "请按实际血糖、饥饿感和健管师反馈调整。"),
            "importance": importance
        })
        items.append(item)

    if not items:
        return None
    group["items"] = items
    return group


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
        if group.get("group_type") == "weekly_meal_plan":
            errors.extend(_validate_weekly_meal_plan(group, group_index))
    return errors


def _validate_weekly_meal_plan(group, group_index):
    errors = []
    items = group.get("items") or []
    if len(items) != 7:
        errors.append(f"groups[{group_index}] weekly_meal_plan 必须包含 7 天菜谱")

    for item_index, item in enumerate(items):
        for field in ("day", "daily_total_kcal", "daily_total_protein_g", "daily_total_fat_g"):
            if field not in item:
                errors.append(f"groups[{group_index}].items[{item_index}].{field} 不能为空")
        meals = item.get("meals")
        if not isinstance(meals, list) or not meals:
            errors.append(f"groups[{group_index}].items[{item_index}].meals 必须是非空数组")
            continue

        meal_names = {meal.get("meal_name") for meal in meals if isinstance(meal, dict)}
        missing_meals = REQUIRED_MEALS - meal_names
        if missing_meals:
            errors.append(f"groups[{group_index}].items[{item_index}] 缺少餐次：{','.join(sorted(missing_meals))}")

        for meal_index, meal in enumerate(meals):
            if not isinstance(meal, dict):
                errors.append(f"groups[{group_index}].items[{item_index}].meals[{meal_index}] 必须是对象")
                continue
            foods = meal.get("foods")
            if not isinstance(foods, list) or not foods:
                errors.append(f"groups[{group_index}].items[{item_index}].meals[{meal_index}].foods 必须是非空数组")
                continue
            for food_index, food in enumerate(foods):
                if not isinstance(food, dict):
                    errors.append(f"groups[{group_index}].items[{item_index}].meals[{meal_index}].foods[{food_index}] 必须是对象")
                    continue
                if not food.get("name"):
                    errors.append(f"groups[{group_index}].items[{item_index}].meals[{meal_index}].foods[{food_index}].name 不能为空")
                for field in FOOD_NUMBER_FIELDS:
                    if field not in food:
                        errors.append(f"groups[{group_index}].items[{item_index}].meals[{meal_index}].foods[{food_index}].{field} 不能为空")
    return errors


def main(plan_header=None, group_plan=None, groups=None, meal_plan_group=None, **kwargs) -> dict:
    header = _parse_json(plan_header, {})
    if not isinstance(header, dict):
        header = {}

    normalized_group_plan = _normalize_group_plan(group_plan)
    normalized_groups = _sort_groups_by_plan(
        _normalize_groups(groups),
        normalized_group_plan
    )
    normalized_meal_plan_group = _normalize_meal_plan_group(meal_plan_group)
    if normalized_meal_plan_group:
        normalized_groups.append(normalized_meal_plan_group)

    if not normalized_groups:
        normalized_groups = [{
            "group_title": "饮食总原则",
            "group_type": "advice_list",
            "group_summary": "当前可用素材不足，先输出最小可执行饮食记录建议。",
            "display_style": "list",
            "items": [{
                "item_type": "advice",
                "content": "先记录三餐、加餐和外食情况，再由健管师结合记录细化饮食方案。",
                "focus_point": "当前可用素材不足，先保证方案可渲染，后续需结合饮食记录和复诊结果进一步调整。",
                "importance": "重点执行"
            }]
        }]

    final_plan = {
        "plan_name": _normalize_text(header.get("plan_name"), "饮食健康处方"),
        "plan_title": _normalize_text(header.get("plan_title"), "个性化饮食管理建议"),
        "plan_summary": _normalize_text(
            header.get("plan_summary"),
            "本方案围绕患者当前健康状况和饮食管理需求，提供可执行的饮食调整建议。"
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
