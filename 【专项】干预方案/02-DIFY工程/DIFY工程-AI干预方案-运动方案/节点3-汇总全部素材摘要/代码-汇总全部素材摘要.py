import json


def _parse_summary_text(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        return value.get("summary_text", "") or ""
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed.get("summary_text", "") or ""
        except json.JSONDecodeError:
            return stripped
    return ""


def main(
    medical_goal_summary=None,
    sport_execution_summary=None,
    safety_boundary_summary=None,
    plan_goal_and_requirements: str = "",
    extra_supplement: str = "",
    **kwargs
) -> dict:
    bundle = {
        "medical_goal_summary": _parse_summary_text(medical_goal_summary),
        "sport_execution_summary": _parse_summary_text(sport_execution_summary),
        "safety_boundary_summary": _parse_summary_text(safety_boundary_summary)
    }

    missing = [key for key, value in bundle.items() if not value]

    return {
        "plan_goal_and_requirements": plan_goal_and_requirements or "",
        "extra_supplement": extra_supplement or "",
        "material_summary_bundle": bundle,
        "summary_missing_fields": missing
    }

