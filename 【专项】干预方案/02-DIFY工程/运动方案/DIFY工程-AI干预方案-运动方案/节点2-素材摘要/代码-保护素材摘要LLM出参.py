import json


SUMMARY_FALLBACKS = {
    "medicalGoalSummary": "本节点输入为空或信息不足，暂无可提炼的疾病边界与指标目标摘要。",
    "sportExecutionSummary": "本节点输入为空或信息不足，暂无可提炼的运动能力与执行问题摘要。",
    "safetyBoundarySummary": "本节点输入为空或信息不足，暂无可提炼的运动安全风险与边界摘要。"
}


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
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = text.strip()
    return text if text else fallback


def _extract_summary(parsed, key):
    fallback = SUMMARY_FALLBACKS[key]
    if isinstance(parsed, dict):
        return _normalize_text(parsed.get(key), fallback)
    return fallback


def main(
    llmOutput=None,
    medicalGoalSummary=None,
    sportExecutionSummary=None,
    safetyBoundarySummary=None,
    planGoalAndRequirements: str = "",
    extraSupplement: str = "",
    **kwargs
) -> dict:
    parsed = _parse_json(llmOutput, {})
    if not isinstance(parsed, dict):
        parsed = {}

    direct = {
        "medicalGoalSummary": medicalGoalSummary,
        "sportExecutionSummary": sportExecutionSummary,
        "safetyBoundarySummary": safetyBoundarySummary
    }

    bundle = {}
    for key, directValue in direct.items():
        if directValue not in (None, ""):
            bundle[key] = _normalize_text(directValue, SUMMARY_FALLBACKS[key])
        else:
            bundle[key] = _extract_summary(parsed, key)

    missing = [
        key
        for key, value in bundle.items()
        if value == SUMMARY_FALLBACKS[key]
    ]

    return {
        "planGoalAndRequirements": planGoalAndRequirements or "",
        "extraSupplement": extraSupplement or "",
        "medicalGoalSummary": bundle["medicalGoalSummary"],
        "sportExecutionSummary": bundle["sportExecutionSummary"],
        "safetyBoundarySummary": bundle["safetyBoundarySummary"],
        "materialSummaryBundle": bundle,
        "materialSummaryBundleText": json.dumps(bundle, ensure_ascii=False),
        "summaryMissingFields": missing,
        "summaryMissingFieldsCount": len(missing)
    }
