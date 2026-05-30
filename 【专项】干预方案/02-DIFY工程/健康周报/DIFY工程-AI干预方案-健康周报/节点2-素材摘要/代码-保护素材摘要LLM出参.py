import json


FIELDS = (
    "metricTrendSummary",
    "dietExerciseSummary",
    "riskAndFollowupSummary",
)


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


def _text(value, fallback):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def main(llmText=None, text=None, **kwargs) -> dict:
    parsed = _parse_json(llmText if llmText is not None else text, {})
    if not isinstance(parsed, dict):
        parsed = {}

    bundle = {
        "metricTrendSummary": _text(parsed.get("metricTrendSummary"), "近7天指标记录不足，暂无法形成稳定趋势判断。"),
        "dietExerciseSummary": _text(parsed.get("dietExerciseSummary"), "近7天饮食和运动记录不足，暂按记录缺失处理。"),
        "riskAndFollowupSummary": _text(parsed.get("riskAndFollowupSummary"), "近7天随访、取药或异常风险信息不足，需继续补充记录。"),
    }
    return {
        "materialSummaryBundle": bundle,
        "materialSummaryBundleText": json.dumps(bundle, ensure_ascii=False),
        **bundle,
    }
