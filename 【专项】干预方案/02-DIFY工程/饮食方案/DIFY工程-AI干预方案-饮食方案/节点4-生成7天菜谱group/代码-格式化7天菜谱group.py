import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}
REQUIRED_MEALS = ("早餐", "午餐", "晚餐")
MEAL_NAME_PREFIXES = ("早餐", "午餐", "晚餐", "加餐", "夜班加餐")
NUMBER_FIELDS = (
    "dailyTotalKcal",
    "dailyTotalProteinG",
    "dailyTotalFatG",
    "dailyTotalCarbsG",
    "estimatedEnergyDeficitKcal",
    "mealTotalKcal",
    "mealTotalProteinG",
    "mealTotalFatG",
    "mealTotalCarbsG",
    "amountG",
    "kcal",
    "proteinG",
    "fatG",
    "carbsG",
)
NUTRITION_TOTAL_FIELDS = (
    ("kcal", "mealTotalKcal", "dailyTotalKcal"),
    ("proteinG", "mealTotalProteinG", "dailyTotalProteinG"),
    ("fatG", "mealTotalFatG", "dailyTotalFatG"),
    ("carbsG", "mealTotalCarbsG", "dailyTotalCarbsG"),
)


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


def _first_object(*values):
    for value in values:
        parsed = _parse_json(value, None)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("text"), str):
                nested = _parse_json(parsed.get("text"), None)
                if isinstance(nested, dict):
                    return nested
            return parsed
    return {}


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


def _normalize_importance(value, fallback="重点执行"):
    importance = _normalize_text(value, fallback)
    return importance if importance in ALLOWED_IMPORTANCE else fallback


def _sum_number(items, key):
    total = round(sum(_normalize_number(item.get(key)) for item in items if isinstance(item, dict)), 1)
    return int(total) if isinstance(total, float) and total.is_integer() else total


def _recalculate_meal_totals(meal):
    foods = meal.get("foods", []) or []
    for food_key, meal_key, _daily_key in NUTRITION_TOTAL_FIELDS:
        meal[meal_key] = _sum_number(foods, food_key)
    return meal


def _recalculate_daily_totals(item):
    meals = item.get("meals", []) or []
    for _food_key, meal_key, daily_key in NUTRITION_TOTAL_FIELDS:
        item[daily_key] = _sum_number(meals, meal_key)
    return item


def _normalize_meal_name(value):
    raw_name = _normalize_text(value, "")
    if not raw_name:
        return "", ""
    for prefix in MEAL_NAME_PREFIXES:
        if raw_name == prefix:
            return prefix, ""
        if raw_name.startswith(prefix):
            scene = raw_name[len(prefix):].strip()
            scene = scene.strip("（）()：: -")
            return prefix, scene
    return raw_name, ""


def _normalize_food(food, warnings, dayIndex, mealName):
    if not isinstance(food, dict):
        warnings.append(f"第{dayIndex}天{mealName}存在非对象食物，已跳过。")
        return None
    name = _normalize_text(food.get("name"), "")
    if not name:
        warnings.append(f"第{dayIndex}天{mealName}存在缺少 name 的食物，已跳过。")
        return None

    output = {
        key: value
        for key, value in food.items()
        if key not in ("name", "amountG", "kcal", "proteinG", "fatG", "carbsG")
    }
    output.update({
        "name": name,
        "amountG": _normalize_number(food.get("amountG")),
        "kcal": _normalize_number(food.get("kcal")),
        "proteinG": _normalize_number(food.get("proteinG")),
        "fatG": _normalize_number(food.get("fatG")),
        "carbsG": _normalize_number(food.get("carbsG")),
    })
    return output


def _normalize_meal(meal, warnings, dayIndex):
    if not isinstance(meal, dict):
        warnings.append(f"第{dayIndex}天存在非对象餐次，已跳过。")
        return None

    mealName, extracted_scene = _normalize_meal_name(meal.get("mealName"))
    if not mealName:
        warnings.append(f"第{dayIndex}天存在缺少 mealName 的餐次，已跳过。")
        return None

    output = {
        key: value
        for key, value in meal.items()
        if key not in ("mealName", "mealTotalKcal", "mealTotalProteinG", "mealTotalFatG", "mealTotalCarbsG", "foods")
    }
    output.update({
        "mealName": mealName,
        "mealTotalKcal": _normalize_number(meal.get("mealTotalKcal")),
        "mealTotalProteinG": _normalize_number(meal.get("mealTotalProteinG")),
        "mealTotalFatG": _normalize_number(meal.get("mealTotalFatG")),
        "mealTotalCarbsG": _normalize_number(meal.get("mealTotalCarbsG")),
    })
    mealScene = _normalize_text(meal.get("mealScene"), extracted_scene)
    if mealScene:
        output["mealScene"] = mealScene

    foods = []
    for food in meal.get("foods", []) or []:
        normalized = _normalize_food(food, warnings, dayIndex, mealName)
        if normalized:
            foods.append(normalized)
    if not foods:
        warnings.append(f"第{dayIndex}天{mealName}缺少有效 foods。")
    output["foods"] = foods
    _recalculate_meal_totals(output)
    return output


def _normalize_daily_item(item, warnings, index):
    if not isinstance(item, dict):
        warnings.append(f"第{index}个菜谱 item 不是对象，已跳过。")
        return None

    day = _normalize_number(item.get("day"), index)
    dayIndex = day if isinstance(day, int) else index
    content = _normalize_text(item.get("content"), "")
    title = _normalize_text(item.get("title"), f"第{dayIndex}天")
    if not content:
        content = title

    output = {
        key: value
        for key, value in item.items()
        if key not in (
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
    }
    output.update({
        "itemType": "dailyMealPlan",
        "day": day,
        "title": title,
        "content": content,
        "focusPoint": _normalize_text(item.get("focusPoint"), "请按实际血糖、饥饿感和健管师反馈调整。"),
        "importance": _normalize_importance(item.get("importance")),
        "dailyTotalKcal": _normalize_number(item.get("dailyTotalKcal")),
        "dailyTotalProteinG": _normalize_number(item.get("dailyTotalProteinG")),
        "dailyTotalFatG": _normalize_number(item.get("dailyTotalFatG")),
        "dailyTotalCarbsG": _normalize_number(item.get("dailyTotalCarbsG")),
    })
    if "estimatedEnergyDeficitKcal" in item:
        output["estimatedEnergyDeficitKcal"] = _normalize_number(item.get("estimatedEnergyDeficitKcal"))

    meals = []
    for meal in item.get("meals", []) or []:
        normalized = _normalize_meal(meal, warnings, dayIndex)
        if normalized:
            meals.append(normalized)
    mealNames = {meal.get("mealName") for meal in meals}
    missingMeals = [mealName for mealName in REQUIRED_MEALS if mealName not in mealNames]
    if missingMeals:
        warnings.append(f"第{dayIndex}天缺少餐次：{','.join(missingMeals)}。")
    output["meals"] = meals
    _recalculate_daily_totals(output)
    return output


def _normalize_meal_plan_group(value, expected_count=7):
    warnings = []
    raw = _parse_json(value, {})
    if isinstance(raw, dict) and "mealPlanGroup" in raw:
        raw = raw.get("mealPlanGroup")
    if not isinstance(raw, dict):
        raw = {}
        warnings.append("未解析到 mealPlanGroup 对象，已输出空菜谱分组。")

    group = {
        key: value
        for key, value in raw.items()
        if key not in ("groupTitle", "groupType", "groupSummary", "displayStyle", "items", "dietPlanGoal")
    }
    group.update({
        "groupTitle": _normalize_text(raw.get("groupTitle"), "最近7天饮食执行菜谱"),
        "groupType": "weeklyMealPlan",
        "groupSummary": _normalize_text(raw.get("groupSummary"), "最近7天三餐执行安排。"),
        "displayStyle": "weeklyMealPlan",
    })

    items = []
    for index, item in enumerate(raw.get("items", []) or [], start=1):
        normalized = _normalize_daily_item(item, warnings, index)
        if normalized:
            items.append(normalized)
    items = sorted(items, key=lambda item: item.get("day", 999))
    if expected_count and len(items) != expected_count:
        warnings.append(f"weeklyMealPlan 当前包含 {len(items)} 天，期望 {expected_count} 天。")
    group["items"] = items[:7]
    return group, warnings


def _merge_groups(groups, warnings):
    merged = {
        "groupTitle": "最近7天饮食执行菜谱",
        "groupType": "weeklyMealPlan",
        "groupSummary": "最近7天三餐执行安排。",
        "displayStyle": "weeklyMealPlan",
        "items": []
    }
    seenDays = set()

    for group in groups:
        for key, value in group.items():
            if key == "items" or key == "dietPlanGoal":
                continue
            if key not in merged or not merged.get(key):
                merged[key] = value
        for item in group.get("items", []) or []:
            day = item.get("day")
            if day in seenDays:
                warnings.append(f"第{day}天重复，已保留首次出现的菜谱。")
                continue
            seenDays.add(day)
            merged["items"].append(item)

    merged["items"] = sorted(merged["items"], key=lambda item: item.get("day", 999))
    actualDays = [item.get("day") for item in merged["items"]]
    missingDays = [day for day in range(1, 8) if day not in actualDays]
    if missingDays:
        warnings.append(f"weeklyMealPlan 缺少天数：{','.join(str(day) for day in missingDays)}。")
    return merged


def main(
    mealPlanGroup=None,
    mealPlanGroup1To3=None,
    mealPlanGroup4To7=None,
    text=None,
    text1To3=None,
    text4To7=None,
    llmText=None,
    llmOutput=None,
    **kwargs
) -> dict:
    partSources = [
        _first_object(mealPlanGroup1To3, text1To3),
        _first_object(mealPlanGroup4To7, text4To7),
    ]
    partSources = [source for source in partSources if source]

    warnings = []
    if partSources:
        formattedParts = []
        for source in partSources:
            group, partWarnings = _normalize_meal_plan_group(source, expected_count=0)
            formattedParts.append(group)
            warnings.extend(partWarnings)
        formattedGroup = _merge_groups(formattedParts, warnings)
        if len(formattedGroup.get("items", [])) != 7:
            warnings.append(f"weeklyMealPlan 合并后包含 {len(formattedGroup.get('items', []))} 天，期望 7 天。")
    else:
        raw = _first_object(mealPlanGroup, text, llmText, llmOutput, kwargs)
        formattedGroup, warnings = _normalize_meal_plan_group(raw)

    return {
        "mealPlanGroup": _json_text(formattedGroup),
        "formattedMealPlanGroupJson": _json_text({"mealPlanGroup": formattedGroup}),
        "mealPlanDaysCount": len(formattedGroup.get("items", [])),
        "formatWarnings": _json_text(warnings),
    }
