import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}
REQUIRED_MEALS = {"早餐", "午餐", "晚餐"}
FOOD_NUMBER_FIELDS = ("amountG", "kcal", "proteinG", "fatG", "carbsG")
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
    "dailyTotalCarbsG",
    "estimatedEnergyDeficitKcal",
    "meals",
)
MEAL_FIELDS = (
    "mealName",
    "mealScene",
    "mealTotalKcal",
    "mealTotalProteinG",
    "mealTotalFatG",
    "mealTotalCarbsG",
    "foods",
)
FOOD_FIELDS = ("name", "amountG", "kcal", "proteinG", "fatG", "carbsG")


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


def _normalize_number(value, fallback=0):
    if value is None or value == "":
        return fallback
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return value
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return fallback
    return int(number) if number.is_integer() else number


def _sum_number(items, key):
    return sum(_normalize_number(item.get(key)) for item in items if isinstance(item, dict))


def _recalculate_weekly_meal_plan_carbs(group):
    if not isinstance(group, dict) or group.get("groupType") != "weeklyMealPlan":
        return group
    for item in group.get("items", []) or []:
        if not isinstance(item, dict):
            continue
        meals = item.get("meals", []) or []
        for meal in meals:
            if not isinstance(meal, dict):
                continue
            meal["mealTotalCarbsG"] = _sum_number(meal.get("foods", []) or [], "carbsG")
        item["dailyTotalCarbsG"] = _sum_number(meals, "mealTotalCarbsG")
    return group


def _normalize_group_plan(groupPlan):
    parsed = _parse_json(groupPlan, {})
    if isinstance(parsed, dict):
        plan = parsed.get("groupPlan", [])
    elif isinstance(parsed, list):
        plan = parsed
    else:
        plan = []

    normalized = []
    for item in plan:
        if not isinstance(item, dict):
            continue
        title = _normalize_text(item.get("groupTitle"), "")
        if not title:
            continue
        normalized.append({
            "groupTitle": title,
            "groupFocus": _normalize_text(item.get("groupFocus"), "")
        })
    return normalized


def _normalize_groups(groups):
    parsed = _parse_json(groups, {})
    if isinstance(parsed, dict):
        rawGroups = parsed.get("groups", [])
    elif isinstance(parsed, list):
        rawGroups = parsed
    else:
        rawGroups = []

    normalized = []
    for group in rawGroups:
        if not isinstance(group, dict):
            continue
        title = _normalize_text(group.get("groupTitle"), "")
        if not title:
            continue
        groupOutput = {
            key: value
            for key, value in group.items()
            if key not in ("items", "groupTitle", "groupType", "groupSummary", "displayStyle")
        }
        groupOutput.update({
            "groupTitle": title,
            "groupType": _normalize_text(group.get("groupType"), "adviceList"),
            "groupSummary": _normalize_text(group.get("groupSummary"), ""),
            "displayStyle": _normalize_text(group.get("displayStyle"), "list")
        })

        items = []
        for item in group.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            content = _normalize_text(item.get("content"), "")
            focusPoint = _normalize_text(item.get("focusPoint"), "")
            if not content:
                continue
            importance = _normalize_text(item.get("importance"), "常规建议")
            if importance not in ALLOWED_IMPORTANCE:
                importance = "常规建议"
            itemOutput = {
                key: value
                for key, value in item.items()
                if key not in ("itemType", "content", "focusPoint", "importance")
            }
            itemOutput.update({
                "itemType": _normalize_text(item.get("itemType"), "advice"),
                "content": content,
                "focusPoint": focusPoint or "请结合后续记录和健管师评估进一步调整。",
                "importance": importance
            })
            items.append(itemOutput)

        if items:
            groupOutput["items"] = items
            normalized.append(groupOutput)
    return normalized


def _normalize_meal_plan_group(mealPlanGroup):
    parsed = _parse_json(mealPlanGroup, {})
    if isinstance(parsed, dict) and "mealPlanGroup" in parsed:
        parsed = parsed.get("mealPlanGroup")
    if not isinstance(parsed, dict):
        return None

    group = {
        key: value
        for key, value in parsed.items()
        if key not in ("groupTitle", "groupType", "groupSummary", "displayStyle", "items", "dietPlanGoal")
    }
    group.update({
        "groupTitle": _normalize_text(parsed.get("groupTitle"), "最近7天饮食执行菜谱"),
        "groupType": "weeklyMealPlan",
        "groupSummary": _normalize_text(parsed.get("groupSummary"), ""),
        "displayStyle": _normalize_text(parsed.get("displayStyle"), "weeklyMealPlan")
    })

    items = []
    for rawItem in parsed.get("items", []) or []:
        if not isinstance(rawItem, dict):
            continue
        content = _normalize_text(rawItem.get("content"), "")
        if not content:
            continue
        importance = _normalize_text(rawItem.get("importance"), "重点执行")
        if importance not in ALLOWED_IMPORTANCE:
            importance = "重点执行"
        item = {
            key: value
            for key, value in rawItem.items()
            if key not in ("itemType", "content", "focusPoint", "importance")
        }
        item.update({
            "itemType": "dailyMealPlan",
            "content": content,
            "focusPoint": _normalize_text(rawItem.get("focusPoint"), "请按实际血糖、饥饿感和健管师反馈调整。"),
            "importance": importance
        })
        items.append(item)

    if not items:
        return None
    group["items"] = items
    group = _recalculate_weekly_meal_plan_carbs(group)
    return group


def _sort_groups_by_plan(groups, groupPlan):
    if not groupPlan:
        return groups
    order = {item["groupTitle"]: index for index, item in enumerate(groupPlan)}
    return sorted(groups, key=lambda group: order.get(group["groupTitle"], 999))


def _field_order(base_fields, objects):
    extras = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        for key in obj.keys():
            if key not in base_fields and key not in extras:
                extras.append(key)
    return list(base_fields) + extras


def _empty_value_for_key(key, objects):
    for obj in objects:
        if not isinstance(obj, dict) or key not in obj:
            continue
        value = obj.get(key)
        if isinstance(value, list):
            return []
        if isinstance(value, dict):
            return {}
    return ""


def _align_object_fields(obj, fields, objects):
    return {
        field: obj.get(field, _empty_value_for_key(field, objects))
        for field in fields
    }


def _align_food_fields(foods):
    if not isinstance(foods, list):
        return foods
    fields = _field_order(FOOD_FIELDS, foods)
    return [
        _align_object_fields(food, fields, foods) if isinstance(food, dict) else food
        for food in foods
    ]


def _align_meal_fields(items):
    meals = [
        meal
        for item in items
        if isinstance(item, dict)
        for meal in item.get("meals", []) or []
        if isinstance(meal, dict)
    ]
    if not meals:
        return

    fields = _field_order(MEAL_FIELDS, meals)
    for item in items:
        if not isinstance(item, dict):
            continue
        itemMeals = item.get("meals")
        if not isinstance(itemMeals, list):
            continue
        alignedMeals = []
        for meal in itemMeals:
            if isinstance(meal, dict):
                meal = dict(meal)
                meal["foods"] = _align_food_fields(meal.get("foods", []))
                alignedMeals.append(_align_object_fields(meal, fields, meals))
            else:
                alignedMeals.append(meal)
        item["meals"] = alignedMeals


def _align_output_fields(plan):
    groups = plan.get("groups")
    if not isinstance(groups, list):
        return plan

    groupFields = _field_order(GROUP_FIELDS, groups)
    items = [
        item
        for group in groups
        if isinstance(group, dict)
        for item in group.get("items", []) or []
        if isinstance(item, dict)
    ]
    itemFields = _field_order(ITEM_FIELDS, items)

    _align_meal_fields(items)

    alignedGroups = []
    for group in groups:
        if not isinstance(group, dict):
            alignedGroups.append(group)
            continue
        alignedItems = [
            _align_object_fields(item, itemFields, items) if isinstance(item, dict) else item
            for item in group.get("items", []) or []
        ]
        normalizedGroup = dict(group)
        normalizedGroup["items"] = alignedItems
        alignedGroups.append(_align_object_fields(normalizedGroup, groupFields, groups))

    plan["groups"] = alignedGroups
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
        if not group.get("groupTitle"):
            errors.append(f"groups[{groupIndex}].groupTitle 不能为空")
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
        if group.get("groupType") == "weeklyMealPlan":
            errors.extend(_validate_weekly_meal_plan(group, groupIndex))
    return errors


def _validate_weekly_meal_plan(group, groupIndex):
    errors = []
    items = group.get("items") or []
    if len(items) != 7:
        errors.append(f"groups[{groupIndex}] weeklyMealPlan 必须包含 7 天菜谱")

    for itemIndex, item in enumerate(items):
        for field in ("day", "dailyTotalKcal", "dailyTotalProteinG", "dailyTotalFatG", "dailyTotalCarbsG"):
            if field not in item:
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].{field} 不能为空")
        meals = item.get("meals")
        if not isinstance(meals, list) or not meals:
            errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals 必须是非空数组")
            continue

        mealNames = {meal.get("mealName") for meal in meals if isinstance(meal, dict)}
        missingMeals = REQUIRED_MEALS - mealNames
        if missingMeals:
            errors.append(f"groups[{groupIndex}].items[{itemIndex}] 缺少餐次：{','.join(sorted(missingMeals))}")

        for mealIndex, meal in enumerate(meals):
            if not isinstance(meal, dict):
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}] 必须是对象")
                continue
            for field in ("mealTotalKcal", "mealTotalProteinG", "mealTotalFatG", "mealTotalCarbsG"):
                if field not in meal:
                    errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}].{field} 不能为空")
            foods = meal.get("foods")
            if not isinstance(foods, list) or not foods:
                errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}].foods 必须是非空数组")
                continue
            for foodIndex, food in enumerate(foods):
                if not isinstance(food, dict):
                    errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}].foods[{foodIndex}] 必须是对象")
                    continue
                if not food.get("name"):
                    errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}].foods[{foodIndex}].name 不能为空")
                for field in FOOD_NUMBER_FIELDS:
                    if field not in food:
                        errors.append(f"groups[{groupIndex}].items[{itemIndex}].meals[{mealIndex}].foods[{foodIndex}].{field} 不能为空")
    return errors


def _normalize_plan_header(planHeader, planName, planTitle, planSummary, executionPoints):
    header = _parse_json(planHeader, {})
    if not isinstance(header, dict):
        header = {}
    if header:
        return header

    return {
        "planName": _normalize_text(planName, ""),
        "planTitle": _normalize_text(planTitle, ""),
        "planSummary": _normalize_text(planSummary, ""),
        "executionPoints": _normalize_text(executionPoints, "")
    }


def main(
    planHeader=None,
    groupPlan=None,
    groups=None,
    mealPlanGroup=None,
    planName=None,
    planTitle=None,
    planSummary=None,
    executionPoints=None,
    **kwargs
) -> dict:
    header = _normalize_plan_header(
        planHeader,
        planName,
        planTitle,
        planSummary,
        executionPoints
    )

    normalizedGroupPlan = _normalize_group_plan(groupPlan)
    normalizedGroups = _sort_groups_by_plan(
        _normalize_groups(groups),
        normalizedGroupPlan
    )
    normalizedMealPlanGroup = _normalize_meal_plan_group(mealPlanGroup)
    if normalizedMealPlanGroup:
        normalizedGroups.append(normalizedMealPlanGroup)

    if not normalizedGroups:
        normalizedGroups = [{
            "groupTitle": "饮食总原则",
            "groupType": "adviceList",
            "groupSummary": "当前可用素材不足，先输出最小可执行饮食记录建议。",
            "displayStyle": "list",
            "items": [{
                "itemType": "advice",
                "content": "先记录三餐、加餐和外食情况，再由健管师结合记录细化饮食方案。",
                "focusPoint": "当前可用素材不足，先保证方案可渲染，后续需结合饮食记录和复诊结果进一步调整。",
                "importance": "重点执行"
            }]
        }]

    finalPlan = {
        "planName": _normalize_text(header.get("planName"), "饮食健康处方"),
        "planTitle": _normalize_text(header.get("planTitle"), "个性化饮食管理建议"),
        "planSummary": _normalize_text(
            header.get("planSummary"),
            "本方案围绕患者当前健康状况和饮食管理需求，提供可执行的饮食调整建议。"
        ),
        "executionPoints": _normalize_text(
            header.get("executionPoints"),
            "优先落实重点执行条目；如出现明显不适、连续指标异常或与医生治疗要求冲突，应及时联系医生或健管师。"
        ),
        "groups": normalizedGroups
    }
    finalPlan = _align_output_fields(finalPlan)

    validationErrors = _validate_plan(finalPlan)
    finalPlanJsonText = json.dumps(finalPlan, ensure_ascii=False)

    return {
        "finalPlanJsonText": finalPlanJsonText,
        "validationErrors": json.dumps(validationErrors, ensure_ascii=False),
        "validationErrorsCount": len(validationErrors),
        "groupsCount": len(normalizedGroups)
    }
