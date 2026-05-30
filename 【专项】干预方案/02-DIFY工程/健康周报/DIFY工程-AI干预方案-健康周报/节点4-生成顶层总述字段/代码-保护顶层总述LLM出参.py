import json


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
    header = {
        "planName": _text(parsed.get("planName"), "健康周报"),
        "planTitle": _text(parsed.get("planTitle"), "最近7天健康情况总结"),
        "planSummary": _text(parsed.get("planSummary"), "本周报围绕患者最近7天指标变化、饮食运动执行、随访和用药相关信息，形成阶段性健康总结。"),
        "executionPoints": _text(parsed.get("executionPoints"), "先看指标是否连续异常，再看饮食运动记录是否稳定；如近7天记录不足，应补齐监测和行为记录，并把异常情况及时反馈给医生或健管师。"),
    }
    return {
        "planHeader": json.dumps(header, ensure_ascii=False),
        **header,
    }
