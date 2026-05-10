import json


def _parse_json_value(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default


def _ensure_list(value):
    parsed = _parse_json_value(value, [])
    return parsed if isinstance(parsed, list) else []


def _ensure_dict(value):
    parsed = _parse_json_value(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _limit_records(records, max_count=80):
    records = records if isinstance(records, list) else []
    return records[:max_count]


def main(
    plan_type: str = "sport",
    plan_goal_and_requirements: str = "",
    extra_supplement: str = "",
    basic_profile=None,
    disease_profile=None,
    followup_records_last_1y=None,
    metric_records_last_1y=None,
    diet_records_last_1y=None,
    exercise_records_last_1y=None,
    med_pickup_records_1y=None,
    active_control_goals=None,
    **kwargs
) -> dict:
    basic_profile = _ensure_dict(basic_profile)
    disease_profile = _ensure_dict(disease_profile)
    followup_records = _limit_records(_ensure_list(followup_records_last_1y), 60)
    metric_records = _limit_records(_ensure_list(metric_records_last_1y), 120)
    diet_records = _limit_records(_ensure_list(diet_records_last_1y), 80)
    exercise_records = _limit_records(_ensure_list(exercise_records_last_1y), 120)
    medication_records = _limit_records(_ensure_list(med_pickup_records_1y), 80)
    active_goals = _limit_records(_ensure_list(active_control_goals), 30)
    normalized_plan_type = (plan_type or "sport").strip().lower()

    common = {
        "plan_type": normalized_plan_type,
        "plan_goal_and_requirements": plan_goal_and_requirements or "",
        "extra_supplement": extra_supplement or ""
    }

    return {
        "medical_goal_context": {
            **common,
            "basic_profile": basic_profile,
            "disease_profile": disease_profile,
            "metric_records_last_1y": metric_records,
            "active_control_goals": active_goals
        },
        "sport_execution_context": {
            **common,
            "basic_profile": basic_profile,
            "followup_records_last_1y": followup_records,
            "exercise_records_last_1y": exercise_records,
            "diet_records_last_1y": diet_records
        },
        "safety_boundary_context": {
            **common,
            "basic_profile": basic_profile,
            "disease_profile": disease_profile,
            "metric_records_last_1y": metric_records,
            "followup_records_last_1y": followup_records,
            "exercise_records_last_1y": exercise_records,
            "med_pickup_records_1y": medication_records,
            "active_control_goals": active_goals
        },
        "plan_goal_and_requirements": plan_goal_and_requirements or "",
        "extra_supplement": extra_supplement or "",
        "plan_type": normalized_plan_type,
        "route_warning": "" if normalized_plan_type == "sport" else "当前工程为运动方案工程，建议确认 plan_type 是否应为 sport。",
        "input_stats": {
            "followup_records_count": len(followup_records),
            "metric_records_count": len(metric_records),
            "diet_records_count": len(diet_records),
            "exercise_records_count": len(exercise_records),
            "med_pickup_records_count": len(medication_records),
            "active_control_goals_count": len(active_goals)
        }
    }

