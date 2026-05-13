import json


def _camelize_key(key):
    if not isinstance(key, str) or "_" not in key:
        return key
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)


def _camelize_keys(value):
    if isinstance(value, list):
        return [_camelize_keys(item) for item in value]
    if isinstance(value, dict):
        return {
            _camelize_key(key): _camelize_keys(item)
            for key, item in value.items()
        }
    return value


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
    if isinstance(parsed, list):
        return _camelize_keys(parsed)
    if isinstance(parsed, dict):
        return [_camelize_keys(parsed)]
    if value is None or value == "":
        return []
    return [{"rawText": str(value)}]


def _ensure_dict(value):
    parsed = _parse_json_value(value, {})
    if isinstance(parsed, dict):
        return _camelize_keys(parsed)
    if value is None or value == "":
        return {}
    return {"rawText": str(value)}


def _limit_records(records, max_count=80):
    records = records if isinstance(records, list) else []
    return records[:max_count]


def _to_json_text(value):
    return json.dumps(value, ensure_ascii=False)


def main(
    planType: str = "sport",
    planGoalAndRequirements: str = "",
    extraSupplement: str = "",
    basicProfile=None,
    diseaseProfile=None,
    followupRecordsLast1y=None,
    metricRecordsLast1y=None,
    dietRecordsLast1y=None,
    exerciseRecordsLast1y=None,
    medPickupRecords1y=None,
    activeControlGoals=None,
    **kwargs
) -> dict:
    basicProfile = _ensure_dict(basicProfile)
    diseaseProfile = _ensure_dict(diseaseProfile)
    followupRecords = _limit_records(_ensure_list(followupRecordsLast1y), 60)
    metricRecords = _limit_records(_ensure_list(metricRecordsLast1y), 120)
    dietRecords = _limit_records(_ensure_list(dietRecordsLast1y), 80)
    exerciseRecords = _limit_records(_ensure_list(exerciseRecordsLast1y), 120)
    medicationRecords = _limit_records(_ensure_list(medPickupRecords1y), 80)
    activeGoals = _limit_records(_ensure_list(activeControlGoals), 30)
    normalizedPlanType = (planType or "sport").strip().lower()

    common = {
        "planType": normalizedPlanType,
        "planGoalAndRequirements": planGoalAndRequirements or "",
        "extraSupplement": extraSupplement or ""
    }

    medicalGoalContext = {
        **common,
        "basicProfile": basicProfile,
        "diseaseProfile": diseaseProfile,
        "metricRecordsLast1y": metricRecords,
        "activeControlGoals": activeGoals
    }
    sportExecutionContext = {
        **common,
        "basicProfile": basicProfile,
        "followupRecordsLast1y": followupRecords,
        "exerciseRecordsLast1y": exerciseRecords,
        "dietRecordsLast1y": dietRecords
    }
    safetyBoundaryContext = {
        **common,
        "basicProfile": basicProfile,
        "diseaseProfile": diseaseProfile,
        "metricRecordsLast1y": metricRecords,
        "followupRecordsLast1y": followupRecords,
        "exerciseRecordsLast1y": exerciseRecords,
        "medPickupRecords1y": medicationRecords,
        "activeControlGoals": activeGoals
    }
    inputStats = {
        "followupRecordsCount": len(followupRecords),
        "metricRecordsCount": len(metricRecords),
        "dietRecordsCount": len(dietRecords),
        "exerciseRecordsCount": len(exerciseRecords),
        "medPickupRecordsCount": len(medicationRecords),
        "activeControlGoalsCount": len(activeGoals)
    }

    return {
        "medicalGoalContext": _to_json_text(medicalGoalContext),
        "sportExecutionContext": _to_json_text(sportExecutionContext),
        "safetyBoundaryContext": _to_json_text(safetyBoundaryContext),
        "planGoalAndRequirements": planGoalAndRequirements or "",
        "extraSupplement": extraSupplement or "",
        "planType": normalizedPlanType,
        "routeWarning": "" if normalizedPlanType == "sport" else "当前工程为运动方案工程，建议确认 planType 是否应为 sport。",
        "inputStats": _to_json_text(inputStats)
    }
