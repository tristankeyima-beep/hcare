import json


ALLOWED_GOALS = {
    "weightLoss",
    "glucoseControl",
    "metabolicOptimization",
    "postoperativeRecovery",
    "lipidControl",
    "bloodPressureControl",
    "digestiveSupport",
    "renalProtection",
    "generalHealth",
    "mixed"
}

GOAL_LABELS = {
    "weightLoss": "减重",
    "glucoseControl": "控糖",
    "metabolicOptimization": "优化代谢",
    "postoperativeRecovery": "术后康复",
    "lipidControl": "控脂",
    "bloodPressureControl": "控压",
    "digestiveSupport": "胃肠调养",
    "renalProtection": "肾脏保护",
    "generalHealth": "一般健康管理",
    "mixed": "多目标组合"
}

CONTEXT_KEYS = (
    "diseaseAndMetricProfile",
    "dietBehaviorPatterns",
    "executionBarriers",
    "safetyConstraints",
    "energyBalanceClues",
    "medicationRelatedCautions",
    "positiveHabitsToKeep",
    "priorityManagementFocus",
    "missingInformation"
)

SUMMARY_KEYS = (
    "medicalGoalSummary",
    "dietExecutionSummary",
    "safetyEnergySummary"
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
        generationHint = _normalize_text(
            item.get("generationHint"),
            "后续生成时保留安全边界，避免编造输入中没有的事实。"
        )
    else:
        evidence = _normalize_text(item, fallback_evidence)
        impact = "需结合后续节点保守生成方案内容。"
        generationHint = "后续生成时保留安全边界，避免编造输入中没有的事实。"

    return {
        "evidence": evidence,
        "impact": impact,
        "generationHint": generationHint
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
    dietPlanGoal=None,
    dietPlanGoalLabel=None,
    goalBasis=None,
    patientContextPack=None,
    materialSummaryBundle=None,
    text=None,
    llmText=None,
    llmOutput=None,
    **kwargs
) -> dict:
    structuredCandidate = {
        "dietPlanGoal": dietPlanGoal,
        "dietPlanGoalLabel": dietPlanGoalLabel,
        "goalBasis": goalBasis,
        "patientContextPack": patientContextPack,
        "materialSummaryBundle": materialSummaryBundle
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
        kwargs
    )

    warnings = []
    goal = _normalize_text(raw.get("dietPlanGoal"), "generalHealth")
    if goal not in ALLOWED_GOALS:
        warnings.append(f"dietPlanGoal 非法，已兜底为 generalHealth：{goal}")
        goal = "generalHealth"

    label = _normalize_text(raw.get("dietPlanGoalLabel"), GOAL_LABELS.get(goal, "一般健康管理"))
    basis = _normalize_text(
        raw.get("goalBasis"),
        "本次画像目标依据不足，按一般慢病饮食管理保守生成。"
    )
    contextPack = _normalize_context_pack(raw.get("patientContextPack"))
    summaryBundle = _normalize_summary_bundle(raw.get("materialSummaryBundle"))

    formattedProfile = {
        "dietPlanGoal": goal,
        "dietPlanGoalLabel": label,
        "goalBasis": basis,
        "patientContextPack": contextPack,
        "materialSummaryBundle": summaryBundle
    }

    return {
        "dietPlanGoal": goal,
        "dietPlanGoalLabel": label,
        "goalBasis": basis,
        "patientContextPack": _json_text(contextPack),
        "materialSummaryBundle": _json_text(summaryBundle),
        "formattedProfileJson": _json_text(formattedProfile),
        "formatWarnings": _json_text(warnings)
    }
