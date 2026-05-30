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
        "planName": _text(parsed.get("planName"), "复诊复查指导"),
        "planTitle": _text(parsed.get("planTitle"), "个性化复诊复查安排"),
        "planSummary": _text(parsed.get("planSummary"), "本方案围绕患者当前健康状况和复诊复查需求，提供可执行的复诊复查安排。"),
        "executionPoints": _text(parsed.get("executionPoints"), "优先完成重点复查项目；复查结果及时回传给医生或健管师；如出现连续指标异常、明显不适或用药中断，应提前联系医生或健管师。"),
    }
    return {
        "planHeader": json.dumps(header, ensure_ascii=False),
        **header,
    }
