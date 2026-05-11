import json


ALLOWED_GOALS = {
    "weight_loss",
    "glucose_control",
    "metabolic_optimization",
    "postoperative_recovery",
    "lipid_control",
    "blood_pressure_control",
    "digestive_support",
    "renal_protection",
    "general_health",
    "mixed"
}

GOAL_LABELS = {
    "weight_loss": "减重",
    "glucose_control": "控糖",
    "metabolic_optimization": "优化代谢",
    "postoperative_recovery": "术后康复",
    "lipid_control": "控脂",
    "blood_pressure_control": "控压",
    "digestive_support": "胃肠调养",
    "renal_protection": "肾脏保护",
    "general_health": "一般健康管理",
    "mixed": "多目标组合"
}

CONTEXT_KEYS = (
    "disease_and_metric_profile",
    "diet_behavior_patterns",
    "execution_barriers",
    "safety_constraints",
    "energy_balance_clues",
    "medication_related_cautions",
    "positive_habits_to_keep",
    "priority_management_focus",
    "missing_information"
)

SUMMARY_KEYS = (
    "medical_goal_summary",
    "diet_execution_summary",
    "safety_energy_summary"
)


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


def _normalize_context_item(item, fallback_evidence):
    if isinstance(item, dict):
        evidence = _normalize_text(item.get("evidence"), fallback_evidence)
        impact = _normalize_text(item.get("impact"), "需结合后续节点保守生成方案内容。")
        generation_hint = _normalize_text(
            item.get("generation_hint"),
            "后续生成时保留安全边界，避免编造输入中没有的事实。"
        )
    else:
        evidence = _normalize_text(item, fallback_evidence)
        impact = "需结合后续节点保守生成方案内容。"
        generation_hint = "后续生成时保留安全边界，避免编造输入中没有的事实。"

    return {
        "evidence": evidence,
        "impact": impact,
        "generation_hint": generation_hint
    }


def _normalize_context_list(value, key):
    parsed = _parse_json(value, value)
    items = parsed if isinstance(parsed, list) else []
    fallback = f"{key} 暂无足够结构化证据。"
    normalized = [
        _normalize_context_item(item, fallback)
        for item in items
    ]
    if not normalized:
        normalized = [_normalize_context_item({}, fallback)]
    return normalized[:5]


def _normalize_context_pack(value):
    parsed = _parse_json(value, {})
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        key: _normalize_context_list(parsed.get(key), key)
        for key in CONTEXT_KEYS
    }


def _normalize_summary_bundle(value):
    parsed = _parse_json(value, {})
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        key: _normalize_text(parsed.get(key), "当前可用素材不足，需结合后续记录进一步完善。")
        for key in SUMMARY_KEYS
    }


def main(
    diet_plan_goal=None,
    diet_plan_goal_label=None,
    goal_basis=None,
    patient_context_pack=None,
    material_summary_bundle=None,
    text=None,
    llm_text=None,
    llm_output=None,
    **kwargs
) -> dict:
    structured_candidate = {
        "diet_plan_goal": diet_plan_goal,
        "diet_plan_goal_label": diet_plan_goal_label,
        "goal_basis": goal_basis,
        "patient_context_pack": patient_context_pack,
        "material_summary_bundle": material_summary_bundle
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
        kwargs
    )

    warnings = []
    goal = _normalize_text(raw.get("diet_plan_goal"), "general_health")
    if goal not in ALLOWED_GOALS:
        warnings.append(f"diet_plan_goal 非法，已兜底为 general_health：{goal}")
        goal = "general_health"

    label = _normalize_text(raw.get("diet_plan_goal_label"), GOAL_LABELS.get(goal, "一般健康管理"))
    basis = _normalize_text(
        raw.get("goal_basis"),
        "本次画像目标依据不足，按一般慢病饮食管理保守生成。"
    )
    context_pack = _normalize_context_pack(raw.get("patient_context_pack"))
    summary_bundle = _normalize_summary_bundle(raw.get("material_summary_bundle"))

    formatted_profile = {
        "diet_plan_goal": goal,
        "diet_plan_goal_label": label,
        "goal_basis": basis,
        "patient_context_pack": context_pack,
        "material_summary_bundle": summary_bundle
    }

    return {
        "diet_plan_goal": goal,
        "diet_plan_goal_label": label,
        "goal_basis": basis,
        "patient_context_pack": _json_text(context_pack),
        "material_summary_bundle": _json_text(summary_bundle),
        "formatted_profile_json": _json_text(formatted_profile),
        "format_warnings": _json_text(warnings)
    }
