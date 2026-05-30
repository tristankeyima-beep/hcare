import json


FIELDS = (
    "medicalStatusSummary",
    "reviewNeedSummary",
    "safetyTriggerSummary",
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
        "medicalStatusSummary": _text(parsed.get("medicalStatusSummary"), "暂无可提炼的疾病状态和指标目标信息。"),
        "reviewNeedSummary": _text(parsed.get("reviewNeedSummary"), "暂无可提炼的复诊复查需求信息。"),
        "safetyTriggerSummary": _text(parsed.get("safetyTriggerSummary"), "暂无可提炼的提前就医触发和安全边界信息。"),
    }
    return {
        "materialSummaryBundle": json.dumps(bundle, ensure_ascii=False),
        **bundle,
    }
