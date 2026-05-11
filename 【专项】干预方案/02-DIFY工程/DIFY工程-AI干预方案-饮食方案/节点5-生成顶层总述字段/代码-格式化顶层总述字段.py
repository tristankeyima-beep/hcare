import json


TEXT_FIELDS = ("plan_name", "plan_title", "plan_summary", "execution_points")
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


def _collect_tone_warnings(plan_header):
    warnings = []
    for field in ("plan_title", "plan_summary", "execution_points"):
        text = plan_header.get(field, "")
        for word in PATIENT_TONE_RISK_WORDS:
            if word in text:
                warnings.append(f"{field} 包含偏病历口吻或内部表达：{word}")
    return warnings


def main(
    plan_name=None,
    plan_title=None,
    plan_summary=None,
    execution_points=None,
    text=None,
    llm_text=None,
    llm_output=None,
    **kwargs
) -> dict:
    structured_candidate = {
        "plan_name": plan_name,
        "plan_title": plan_title,
        "plan_summary": plan_summary,
        "execution_points": execution_points,
    }
    has_structured_fields = any(
        value not in (None, "", {}, [])
        for value in structured_candidate.values()
    )
    raw = _first_object(
        structured_candidate if has_structured_fields else None,
        text,
        llm_text,
        llm_output,
        kwargs,
    )

    warnings = []
    plan_header = {
        "plan_name": _normalize_text(raw.get("plan_name"), "饮食健康处方"),
        "plan_title": _normalize_text(raw.get("plan_title"), "个性化饮食管理建议"),
        "plan_summary": _normalize_text(
            raw.get("plan_summary"),
            "这份方案会帮你把饮食调整方向和最近7天执行安排梳理清楚，接下来可以先按重点条目逐步执行。",
        ),
        "execution_points": _normalize_text(
            raw.get("execution_points"),
            "优先落实重点执行条目；饮食调整以循序渐进、可长期坚持为原则；如出现明显不适、连续指标异常或与医生治疗要求冲突，应及时联系医生或健管师。",
        ),
    }

    for field in TEXT_FIELDS:
        if not _normalize_text(raw.get(field), ""):
            warnings.append(f"{field} 为空，已使用默认文案兜底。")
    warnings.extend(_collect_tone_warnings(plan_header))

    return {
        "plan_name": plan_header["plan_name"],
        "plan_title": plan_header["plan_title"],
        "plan_summary": plan_header["plan_summary"],
        "execution_points": plan_header["execution_points"],
        "plan_header": _json_text(plan_header),
        "formatted_plan_header_json": _json_text(plan_header),
        "format_warnings": _json_text(warnings),
    }
