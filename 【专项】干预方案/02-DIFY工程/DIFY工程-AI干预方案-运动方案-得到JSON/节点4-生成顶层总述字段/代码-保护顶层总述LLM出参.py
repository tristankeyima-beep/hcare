import json


DEFAULT_PLAN_HEADER = {
    "planName": "运动健康处方",
    "planTitle": "个性化运动管理建议",
    "planSummary": "本方案围绕患者当前健康状况和运动管理需求，提供可执行的运动调整建议。",
    "executionPoints": "优先落实重点执行条目；运动调整以循序渐进、可长期坚持为原则；如出现明显不适、连续指标异常或与医生治疗要求冲突，应及时联系医生或健管师。"
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
    text = str(value).strip()
    return text if text else fallback


def _pick_llm_output(llmOutput=None, llmText=None):
    if llmOutput not in (None, ""):
        return llmOutput
    return llmText


def main(
    llmOutput=None,
    llmText=None,
    planName: str = "",
    planTitle: str = "",
    planSummary: str = "",
    executionPoints: str = "",
    **kwargs
) -> dict:
    parsed = _parse_json(_pick_llm_output(llmOutput, llmText), {})
    if not isinstance(parsed, dict):
        parsed = {}

    provided = {
        "planName": planName or parsed.get("planName"),
        "planTitle": planTitle or parsed.get("planTitle"),
        "planSummary": planSummary or parsed.get("planSummary"),
        "executionPoints": executionPoints or parsed.get("executionPoints")
    }

    planHeader = {
        "planName": _normalize_text(provided["planName"], DEFAULT_PLAN_HEADER["planName"]),
        "planTitle": _normalize_text(provided["planTitle"], DEFAULT_PLAN_HEADER["planTitle"]),
        "planSummary": _normalize_text(provided["planSummary"], DEFAULT_PLAN_HEADER["planSummary"]),
        "executionPoints": _normalize_text(provided["executionPoints"], DEFAULT_PLAN_HEADER["executionPoints"])
    }

    fallbackFields = [
        key
        for key in DEFAULT_PLAN_HEADER
        if _normalize_text(provided[key], "") == ""
    ]

    return {
        **planHeader,
        "planHeader": planHeader,
        "planHeaderText": json.dumps(planHeader, ensure_ascii=False),
        "fallbackFields": fallbackFields,
        "fallbackFieldsCount": len(fallbackFields)
    }
