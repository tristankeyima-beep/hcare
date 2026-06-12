import json
from datetime import datetime, timedelta, timezone


def _camelize_key(key):
    if not isinstance(key, str) or "_" not in key:
        return key
    parts = key.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)


def _camelize_keys(value):
    if isinstance(value, list):
        return [_camelize_keys(item) for item in value]
    if isinstance(value, dict):
        return {_camelize_key(key): _camelize_keys(item) for key, item in value.items()}
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


def _limit_records(records, max_count=120):
    records = records if isinstance(records, list) else []
    return records[:max_count]


def _parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(timestamp, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:19] if " " in text else text[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _record_datetime(record):
    if not isinstance(record, dict):
        return None
    candidate_keys = (
        "recordTime", "recordDate", "measureTime", "metricTime", "followupTime",
        "followupDate", "mealTime", "exerciseTime", "pickupTime", "createdAt",
        "updatedAt", "date", "time",
    )
    for key in candidate_keys:
        parsed = _parse_datetime(record.get(key))
        if parsed:
            return parsed
    return None


def _latest_datetime(*record_lists):
    latest = None
    for records in record_lists:
        for record in records or []:
            parsed = _record_datetime(record)
            if parsed and (latest is None or parsed > latest):
                latest = parsed
    return latest


def _recent_records(records, reference_dt, days=7):
    if not reference_dt:
        return []
    start_dt = reference_dt - timedelta(days=days)
    recent = []
    undated = []
    for record in records or []:
        parsed = _record_datetime(record)
        if parsed is None:
            undated.append(record)
        elif start_dt <= parsed <= reference_dt:
            recent.append(record)
    return recent if recent else undated[:20]


def _to_json_text(value):
    return json.dumps(value, ensure_ascii=False)


def main(
    planType: str = "report",
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
    followupRecords = _limit_records(_ensure_list(followupRecordsLast1y), 120)
    metricRecords = _limit_records(_ensure_list(metricRecordsLast1y), 160)
    dietRecords = _limit_records(_ensure_list(dietRecordsLast1y), 120)
    exerciseRecords = _limit_records(_ensure_list(exerciseRecordsLast1y), 120)
    medicationRecords = _limit_records(_ensure_list(medPickupRecords1y), 100)
    activeGoals = _limit_records(_ensure_list(activeControlGoals), 30)
    normalizedPlanType = (planType or "report").strip().lower()

    reference_dt = _latest_datetime(metricRecords, dietRecords, exerciseRecords, followupRecords, medicationRecords)
    reportWindow = {
        "label": "最近7天",
        "days": 7,
        "referenceDate": reference_dt.date().isoformat() if reference_dt else "",
        "startDate": (reference_dt - timedelta(days=7)).date().isoformat() if reference_dt else "",
        "windowBasis": "按输入记录中最新日期向前推7天" if reference_dt else "输入记录缺少可识别日期，按近7天记录不足处理",
    }
    recentMetricRecords = _recent_records(metricRecords, reference_dt)
    recentDietRecords = _recent_records(dietRecords, reference_dt)
    recentExerciseRecords = _recent_records(exerciseRecords, reference_dt)
    recentFollowupRecords = _recent_records(followupRecords, reference_dt)
    recentMedicationRecords = _recent_records(medicationRecords, reference_dt)

    common = {
        "planType": normalizedPlanType,
        "planGoalAndRequirements": planGoalAndRequirements or "",
        "extraSupplement": extraSupplement or "",
        "reportWindow": reportWindow,
    }

    metricTrendContext = {
        **common,
        "basicProfile": basicProfile,
        "diseaseProfile": diseaseProfile,
        "metricRecordsRecent7d": recentMetricRecords,
        "metricRecordsLast1y": metricRecords,
        "activeControlGoals": activeGoals,
    }
    dietExerciseContext = {
        **common,
        "dietRecordsRecent7d": recentDietRecords,
        "exerciseRecordsRecent7d": recentExerciseRecords,
        "followupRecordsRecent7d": recentFollowupRecords,
        "dietRecordsLast1y": dietRecords,
        "exerciseRecordsLast1y": exerciseRecords,
    }
    riskAndFollowupContext = {
        **common,
        "basicProfile": basicProfile,
        "diseaseProfile": diseaseProfile,
        "metricRecordsRecent7d": recentMetricRecords,
        "followupRecordsRecent7d": recentFollowupRecords,
        "medPickupRecordsRecent7d": recentMedicationRecords,
        "activeControlGoals": activeGoals,
    }
    inputStats = {
        "reportWindow": reportWindow,
        "followupRecordsCount": len(followupRecords),
        "metricRecordsCount": len(metricRecords),
        "dietRecordsCount": len(dietRecords),
        "exerciseRecordsCount": len(exerciseRecords),
        "medPickupRecordsCount": len(medicationRecords),
        "activeControlGoalsCount": len(activeGoals),
        "recent7dFollowupRecordsCount": len(recentFollowupRecords),
        "recent7dMetricRecordsCount": len(recentMetricRecords),
        "recent7dDietRecordsCount": len(recentDietRecords),
        "recent7dExerciseRecordsCount": len(recentExerciseRecords),
        "recent7dMedPickupRecordsCount": len(recentMedicationRecords),
    }

    return {
        "metricTrendContext": _to_json_text(metricTrendContext),
        "dietExerciseContext": _to_json_text(dietExerciseContext),
        "riskAndFollowupContext": _to_json_text(riskAndFollowupContext),
        "planGoalAndRequirements": planGoalAndRequirements or "",
        "extraSupplement": extraSupplement or "",
        "planType": normalizedPlanType,
        "routeWarning": "" if normalizedPlanType == "report" else "当前工程为健康周报工程，建议确认 planType 是否应为 report。",
        "inputStats": _to_json_text(inputStats),
    }
