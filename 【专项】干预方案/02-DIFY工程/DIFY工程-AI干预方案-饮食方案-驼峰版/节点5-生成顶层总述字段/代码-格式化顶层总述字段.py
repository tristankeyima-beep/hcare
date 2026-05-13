import json


TEXT_FIELDS = ("planName", "planTitle", "planSummary", "executionPoints")
PATIENT_TONE_RISK_WORDS = ("患者", "该患者", "结合患者情况", "制造热量缺口")


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


def _collect_tone_warnings(planHeader):
    warnings = []
    for field in ("planTitle", "planSummary", "executionPoints"):
        text = planHeader.get(field, "")
        for word in PATIENT_TONE_RISK_WORDS:
            if word in text:
                warnings.append(f"{field} 包含偏病历口吻或内部表达：{word}")
    return warnings


def main(
    planName=None,
    planTitle=None,
    planSummary=None,
    executionPoints=None,
    text=None,
    llmText=None,
    llmOutput=None,
    **kwargs
) -> dict:
    structuredCandidate = {
        "planName": planName,
        "planTitle": planTitle,
        "planSummary": planSummary,
        "executionPoints": executionPoints,
    }
    hasStructuredFields = any(
        value not in (None, "", {}, [])
        for value in structuredCandidate.values()
    )
    raw = _first_object(
        structuredCandidate if hasStructuredFields else None,
        text,
        llmText,
        llmOutput,
        kwargs,
    )

    warnings = []
    planHeader = {
        "planName": _normalize_text(raw.get("planName"), "饮食健康处方"),
        "planTitle": _normalize_text(raw.get("planTitle"), "个性化饮食管理建议"),
        "planSummary": _normalize_text(
            raw.get("planSummary"),
            "这份方案会帮你把饮食调整方向和最近7天执行安排梳理清楚，接下来可以先按重点条目逐步执行。",
        ),
        "executionPoints": _normalize_text(
            raw.get("executionPoints"),
            "优先落实重点执行条目；饮食调整以循序渐进、可长期坚持为原则；如出现明显不适、连续指标异常或与医生治疗要求冲突，应及时联系医生或健管师。",
        ),
    }

    for field in TEXT_FIELDS:
        if not _normalize_text(raw.get(field), ""):
            warnings.append(f"{field} 为空，已使用默认文案兜底。")
    warnings.extend(_collect_tone_warnings(planHeader))

    return {
        "planName": planHeader["planName"],
        "planTitle": planHeader["planTitle"],
        "planSummary": planHeader["planSummary"],
        "executionPoints": planHeader["executionPoints"],
        "planHeader": _json_text(planHeader),
        "formattedPlanHeaderJson": _json_text(planHeader),
        "formatWarnings": _json_text(warnings),
    }
