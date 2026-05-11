import json


ALLOWED_IMPORTANCE = {"重点执行", "常规建议", "补充建议"}
REQUIRED_MEALS = ("早餐", "午餐", "晚餐")
MEAL_NAME_PREFIXES = ("早餐", "午餐", "晚餐", "加餐", "夜班加餐")
NUMBER_FIELDS = (
    "daily_total_kcal",
    "daily_total_protein_g",
    "daily_total_fat_g",
    "estimated_energy_deficit_kcal",
    "meal_total_kcal",
    "meal_total_protein_g",
    "meal_total_fat_g",
    "amount_g",
    "kcal",
    "protein_g",
    "fat_g",
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


def _normalize_food(food, warnings, day_index, meal_name):
    if not isinstance(food, dict):
        warnings.append(f"第{day_index}天{meal_name}存在非对象食物，已跳过。")
        return None
    name = _normalize_text(food.get("name"), "")
    if not name:
        warnings.append(f"第{day_index}天{meal_name}存在缺少 name 的食物，已跳过。")
        return None

    output = {
        key: value
        for key, value in food.items()
        if key not in ("name", "amount_g", "kcal", "protein_g", "fat_g")
    }
    output.update({
        "name": name,
        "amount_g": _normalize_number(food.get("amount_g")),
        "kcal": _normalize_number(food.get("kcal")),
        "protein_g": _normalize_number(food.get("protein_g")),
        "fat_g": _normalize_number(food.get("fat_g")),
    })
    return output


def _normalize_meal(meal, warnings, day_index):
    if not isinstance(meal, dict):
        warnings.append(f"第{day_index}天存在非对象餐次，已跳过。")
        return None

    meal_name, extracted_scene = _normalize_meal_name(meal.get("meal_name"))
    if not meal_name:
        warnings.append(f"第{day_index}天存在缺少 meal_name 的餐次，已跳过。")
        return None

    output = {
        key: value
        for key, value in meal.items()
        if key not in ("meal_name", "meal_total_kcal", "meal_total_protein_g", "meal_total_fat_g", "foods")
    }
    output.update({
        "meal_name": meal_name,
        "meal_total_kcal": _normalize_number(meal.get("meal_total_kcal")),
        "meal_total_protein_g": _normalize_number(meal.get("meal_total_protein_g")),
        "meal_total_fat_g": _normalize_number(meal.get("meal_total_fat_g")),
    })
    meal_scene = _normalize_text(meal.get("meal_scene"), extracted_scene)
    if meal_scene:
        output["meal_scene"] = meal_scene

    foods = []
    for food in meal.get("foods", []) or []:
        normalized = _normalize_food(food, warnings, day_index, meal_name)
        if normalized:
            foods.append(normalized)
    if not foods:
        warnings.append(f"第{day_index}天{meal_name}缺少有效 foods。")
    output["foods"] = foods
    return output


def _normalize_daily_item(item, warnings, index):
    if not isinstance(item, dict):
        warnings.append(f"第{index}个菜谱 item 不是对象，已跳过。")
        return None

    day = _normalize_number(item.get("day"), index)
    day_index = day if isinstance(day, int) else index
    content = _normalize_text(item.get("content"), "")
    title = _normalize_text(item.get("title"), f"第{day_index}天")
    if not content:
        content = title

    output = {
        key: value
        for key, value in item.items()
        if key not in (
            "item_type",
            "day",
            "title",
            "content",
            "focus_point",
            "importance",
            "daily_total_kcal",
            "daily_total_protein_g",
            "daily_total_fat_g",
            "estimated_energy_deficit_kcal",
            "meals",
        )
    }
    output.update({
        "item_type": "daily_meal_plan",
        "day": day,
        "title": title,
        "content": content,
        "focus_point": _normalize_text(item.get("focus_point"), "请按实际血糖、饥饿感和健管师反馈调整。"),
        "importance": _normalize_importance(item.get("importance")),
        "daily_total_kcal": _normalize_number(item.get("daily_total_kcal")),
        "daily_total_protein_g": _normalize_number(item.get("daily_total_protein_g")),
        "daily_total_fat_g": _normalize_number(item.get("daily_total_fat_g")),
    })
    if "estimated_energy_deficit_kcal" in item:
        output["estimated_energy_deficit_kcal"] = _normalize_number(item.get("estimated_energy_deficit_kcal"))

    meals = []
    for meal in item.get("meals", []) or []:
        normalized = _normalize_meal(meal, warnings, day_index)
        if normalized:
            meals.append(normalized)
    meal_names = {meal.get("meal_name") for meal in meals}
    missing_meals = [meal_name for meal_name in REQUIRED_MEALS if meal_name not in meal_names]
    if missing_meals:
        warnings.append(f"第{day_index}天缺少餐次：{','.join(missing_meals)}。")
    output["meals"] = meals
    return output


def _normalize_meal_plan_group(value, expected_count=7):
    warnings = []
    raw = _parse_json(value, {})
    if isinstance(raw, dict) and "meal_plan_group" in raw:
        raw = raw.get("meal_plan_group")
    if not isinstance(raw, dict):
        raw = {}
        warnings.append("未解析到 meal_plan_group 对象，已输出空菜谱分组。")

    group = {
        key: value
        for key, value in raw.items()
        if key not in ("group_title", "group_type", "group_summary", "display_style", "items", "diet_plan_goal")
    }
    group.update({
        "group_title": _normalize_text(raw.get("group_title"), "最近7天饮食执行菜谱"),
        "group_type": "weekly_meal_plan",
        "group_summary": _normalize_text(raw.get("group_summary"), "最近7天三餐执行安排。"),
        "display_style": "weekly_meal_plan",
    })

    items = []
    for index, item in enumerate(raw.get("items", []) or [], start=1):
        normalized = _normalize_daily_item(item, warnings, index)
        if normalized:
            items.append(normalized)
    items = sorted(items, key=lambda item: item.get("day", 999))
    if expected_count and len(items) != expected_count:
        warnings.append(f"weekly_meal_plan 当前包含 {len(items)} 天，期望 {expected_count} 天。")
    group["items"] = items[:7]
    return group, warnings


def _merge_groups(groups, warnings):
    merged = {
        "group_title": "最近7天饮食执行菜谱",
        "group_type": "weekly_meal_plan",
        "group_summary": "最近7天三餐执行安排。",
        "display_style": "weekly_meal_plan",
        "items": []
    }
    seen_days = set()

    for group in groups:
        for key, value in group.items():
            if key == "items" or key == "diet_plan_goal":
                continue
            if key not in merged or not merged.get(key):
                merged[key] = value
        for item in group.get("items", []) or []:
            day = item.get("day")
            if day in seen_days:
                warnings.append(f"第{day}天重复，已保留首次出现的菜谱。")
                continue
            seen_days.add(day)
            merged["items"].append(item)

    merged["items"] = sorted(merged["items"], key=lambda item: item.get("day", 999))
    actual_days = [item.get("day") for item in merged["items"]]
    missing_days = [day for day in range(1, 8) if day not in actual_days]
    if missing_days:
        warnings.append(f"weekly_meal_plan 缺少天数：{','.join(str(day) for day in missing_days)}。")
    return merged


def main(
    meal_plan_group=None,
    meal_plan_group_1_3=None,
    meal_plan_group_4_7=None,
    text=None,
    text_1_3=None,
    text_4_7=None,
    llm_text=None,
    llm_output=None,
    **kwargs
) -> dict:
    part_sources = [
        _first_object(meal_plan_group_1_3, text_1_3),
        _first_object(meal_plan_group_4_7, text_4_7),
    ]
    part_sources = [source for source in part_sources if source]

    warnings = []
    if part_sources:
        formatted_parts = []
        for source in part_sources:
            group, part_warnings = _normalize_meal_plan_group(source, expected_count=0)
            formatted_parts.append(group)
            warnings.extend(part_warnings)
        formatted_group = _merge_groups(formatted_parts, warnings)
        if len(formatted_group.get("items", [])) != 7:
            warnings.append(f"weekly_meal_plan 合并后包含 {len(formatted_group.get('items', []))} 天，期望 7 天。")
    else:
        raw = _first_object(meal_plan_group, text, llm_text, llm_output, kwargs)
        formatted_group, warnings = _normalize_meal_plan_group(raw)

    return {
        "meal_plan_group": _json_text(formatted_group),
        "formatted_meal_plan_group_json": _json_text({"meal_plan_group": formatted_group}),
        "meal_plan_days_count": len(formatted_group.get("items", [])),
        "format_warnings": _json_text(warnings),
    }
