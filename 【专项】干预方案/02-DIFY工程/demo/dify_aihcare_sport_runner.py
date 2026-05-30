#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import ssl
import subprocess
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_SOURCE_FILE = PROJECT_ROOT / "运动方案" / "DIFY工程-AI干预方案-运动方案" / "测试数据" / "【入参】运动方案工作流测试入参.json"
DEFAULT_API_BASE = "https://dify.hzmarvel.com/v1"
DEFAULT_RESPONSE_MODE = "streaming"
DEFAULT_USER = "dify-aihcare-sport-chatflow-test"
DEFAULT_QUERY = "请根据基础档案生成运动方案。"
DEFAULT_ENV_NAME = "test"
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
INPUT_FILE_NAME = "入参.json"


class PrepareResult:
    def __init__(self, case_dir, patient_name, input_path, terminal_command):
        self.case_dir = case_dir
        self.patient_name = patient_name
        self.input_path = input_path
        self.terminal_command = terminal_command


def parse_local_time(value):
    return datetime.fromisoformat(value).astimezone(LOCAL_TZ)


def now_local():
    return datetime.now(LOCAL_TZ)


def compact_timestamp(value):
    return value.astimezone(LOCAL_TZ).strftime("%Y%m%d-%H%M%S")


def display_timestamp(value):
    return value.astimezone(LOCAL_TZ).isoformat(timespec="seconds")


def read_json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_file(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def stringify_for_dify(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_maybe_json(value):
    if isinstance(value, str):
        text = value.strip()
        if text and text[0] in "[{":
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return value
    return value


def sanitize_path_part(value, fallback):
    text = str(value or "").strip() or fallback
    text = re.sub(r'[/\\:*?"<>|\r\n\t]+', " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or fallback


def normalize_env_name(value):
    return sanitize_path_part(value or DEFAULT_ENV_NAME, DEFAULT_ENV_NAME)


def env_api_key_name(env_name):
    suffix = re.sub(r"[^A-Za-z0-9]+", "_", str(env_name or DEFAULT_ENV_NAME)).strip("_").upper()
    return f"DIFY_API_KEY_{suffix}" if suffix else "DIFY_API_KEY"


def resolve_api_key(explicit_api_key, env_name):
    if explicit_api_key:
        return explicit_api_key
    env_key = os.environ.get(env_api_key_name(env_name))
    return env_key or os.environ.get("DIFY_API_KEY")


def shell_quote(value):
    text = str(value)
    if re.match(r"^[A-Za-z0-9_./:=@%+\-]+$", text):
        return text
    return '"' + re.sub(r'(["\\$`])', r"\\\1", text) + '"'


def build_run_command(case_dir, env_name=DEFAULT_ENV_NAME, api_base=DEFAULT_API_BASE):
    relative_case = case_dir
    env_name = normalize_env_name(env_name)
    try:
        relative_case = case_dir.relative_to(SCRIPT_DIR)
    except ValueError:
        pass
    return (
        f"cd {shell_quote(SCRIPT_DIR)} && "
        f"{env_api_key_name(env_name)}=\"app-***\" python3 dify_aihcare_sport_runner.py run "
        f"--env-name {shell_quote(env_name)} "
        f"--api-base {shell_quote(api_base)} "
        f"--case-dir {shell_quote(relative_case)}"
    )


def get_nested_value(obj, keys):
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_patient_name(raw_inputs):
    external_name = get_nested_value(raw_inputs, ("externalPatientInfo", "patientName"))
    if external_name:
        return str(external_name)
    for key in ("patientName", "patient_name", "姓名"):
        if raw_inputs.get(key):
            return str(raw_inputs[key])
    basic_profile = parse_maybe_json(raw_inputs.get("basicProfile"))
    profile_name = get_nested_value(basic_profile, ("demographics", "name"))
    return str(profile_name) if profile_name else "未知患者"


def normalize_inputs(raw_input):
    raw_inputs = raw_input.get("inputs") if isinstance(raw_input.get("inputs"), dict) else raw_input
    normalized = dict(raw_inputs)
    for key in ("response_mode", "user", "conversation_id", "query"):
        normalized.pop(key, None)
    normalized["planType"] = normalized.get("planType") or "sport"
    patient_name = extract_patient_name(raw_inputs)
    return {key: stringify_for_dify(value) for key, value in normalized.items()}, patient_name


def prepare_input_file(input_path, output_root=None, now=None, env_name=DEFAULT_ENV_NAME):
    input_path = Path(input_path)
    output_root = Path(output_root) if output_root else SCRIPT_DIR / "userinput"
    now = now or now_local()
    raw_input = read_json_file(input_path)
    inputs, patient_name = normalize_inputs(raw_input)
    env_name = normalize_env_name(env_name)
    safe_patient = sanitize_path_part(patient_name, "未知患者")
    case_dir = output_root / f"{safe_patient}_运动方案_{compact_timestamp(now)}"
    case_dir.mkdir(parents=True, exist_ok=True)
    terminal_command = build_run_command(case_dir, env_name=env_name)
    payload = {
        "metadata": {
            "patientName": patient_name,
            "caseName": "运动方案",
            "defaultEnvironment": env_name,
            "recordedAt": display_timestamp(now),
            "timeZone": "Asia/Shanghai",
            "sourceInput": str(input_path),
        },
        "raw_input": raw_input,
        "dify_payload": {
            "inputs": inputs,
            "query": DEFAULT_QUERY,
            "response_mode": DEFAULT_RESPONSE_MODE,
            "user": DEFAULT_USER,
            "conversation_id": "",
        },
        "terminal_command": terminal_command,
    }
    input_record_path = case_dir / INPUT_FILE_NAME
    write_json_file(input_record_path, payload)
    return PrepareResult(case_dir, patient_name, input_record_path, terminal_command)


def load_case_input(case_dir):
    case_dir = Path(case_dir)
    if not case_dir.is_absolute():
        case_dir = SCRIPT_DIR / case_dir
    return case_dir, read_json_file(case_dir / INPUT_FILE_NAME)


def mask_headers(headers):
    return {
        key: ("Bearer ***" if key.lower() == "authorization" else value)
        for key, value in headers.items()
    }


def empty_record(method, url, headers, body):
    return {
        "startedAt": display_timestamp(now_local()),
        "endedAt": "",
        "timeZone": "Asia/Shanghai",
        "request": {"method": method, "url": url, "headers": mask_headers(headers), "body": body},
        "response": None,
        "events": [],
        "nodeRuns": [],
        "answer": "",
        "messageId": "",
        "conversationId": "",
        "messageEndMetadata": None,
        "finalPlan": None,
        "finalPlanParseError": "",
        "validationSummary": None,
        "environment": None,
        "error": None,
    }


def create_ssl_context():
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()
    if hasattr(ssl, "OP_IGNORE_UNEXPECTED_EOF"):
        context.options |= ssl.OP_IGNORE_UNEXPECTED_EOF
    return context


def parse_sse_block(block):
    event_type = ""
    data_lines = []
    for line in block.splitlines():
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return None
    data_text = "\n".join(data_lines)
    try:
        payload = json.loads(data_text)
    except json.JSONDecodeError:
        payload = data_text
    return {"type": event_type or "message", "payload": payload, "raw": block}


def collect_event_summary(record, event):
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    name = payload.get("event") or event.get("type") or "unknown"
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

    if payload.get("message_id") and not record.get("messageId"):
        record["messageId"] = str(payload["message_id"])
    if payload.get("conversation_id") and not record.get("conversationId"):
        record["conversationId"] = str(payload["conversation_id"])

    if name in ("message", "agent_message", "text_chunk"):
        text = payload.get("answer") or data.get("text") or data.get("answer") or ""
        if text:
            record["answer"] += text
    elif name == "node_started":
        record["nodeRuns"].append({
            "id": data.get("id") or data.get("node_id") or "",
            "title": data.get("title") or data.get("node_type") or "unknown",
            "type": data.get("node_type") or "",
            "status": "running",
            "inputs": None,
            "outputs": None,
        })
    elif name == "node_finished":
        title = data.get("title") or data.get("node_type") or "unknown"
        target = None
        for node in reversed(record["nodeRuns"]):
            if node.get("title") == title and node.get("status") == "running":
                target = node
                break
        if target is None:
            target = {"id": data.get("id") or data.get("node_id") or "", "title": title, "type": data.get("node_type") or ""}
            record["nodeRuns"].append(target)
        target.update({
            "status": data.get("status") or "finished",
            "elapsedSeconds": data.get("elapsed_time"),
            "inputs": data.get("inputs"),
            "processData": data.get("process_data"),
            "outputs": data.get("outputs"),
        })
    elif name == "message_end":
        record["messageEndMetadata"] = payload.get("metadata")


def collect_curl_response(record, stdout, stderr):
    match = re.search(r"\n__DIFY_HTTP_STATUS__:(\d{3})\s*$", stdout)
    status = int(match.group(1)) if match else 0
    body_text = stdout[: match.start()] if match else stdout
    record["response"] = {"status": status, "reason": "", "headers": {}, "body": None, "stderr": stderr.strip()}
    if status >= 400 or not body_text.lstrip().startswith("data:"):
        try:
            record["response"]["body"] = json.loads(body_text)
        except json.JSONDecodeError:
            record["response"]["body"] = body_text
        if status >= 400:
            record["error"] = {"type": "HTTPError", "message": f"HTTP Error {status}"}
        return
    for block in body_text.split("\n\n"):
        event = parse_sse_block(block)
        if not event:
            continue
        record["events"].append(event)
        collect_event_summary(record, event)
    finalize_record(record)


def finalize_record(record):
    final_plan, parse_error = extract_final_plan(record.get("answer") or "")
    record["finalPlan"] = final_plan
    record["finalPlanParseError"] = parse_error or ""
    record["validationSummary"] = validate_final_plan(final_plan) if final_plan else {
        "errors": ["未解析到运动方案最终 JSON"],
        "groupsCount": 0,
        "itemsCount": 0,
        "importantItemsCount": 0,
        "coverageWarnings": [],
    }


def call_dify_chatflow(case_record, api_base, api_key, query=None, transport="curl", env_name=DEFAULT_ENV_NAME):
    started = now_local()
    env_name = normalize_env_name(env_name)
    url = api_base.rstrip("/") + "/chat-messages"
    body = dict(case_record["dify_payload"])
    body["query"] = query or body.get("query") or DEFAULT_QUERY
    body["response_mode"] = DEFAULT_RESPONSE_MODE
    body["conversation_id"] = body.get("conversation_id") or ""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    record = empty_record("POST", url, headers, body)
    record["startedAt"] = display_timestamp(started)
    record["caseMetadata"] = case_record.get("metadata", {})
    record["terminalCommand"] = case_record.get("terminal_command", "")
    record["environment"] = {"name": env_name, "apiBase": api_base.rstrip("/")}
    if transport == "curl":
        call_dify_with_curl(record, url, headers, body)
        record["endedAt"] = display_timestamp(now_local())
        return record

    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        open_kwargs = {"timeout": 300}
        if url.startswith("https://"):
            open_kwargs["context"] = create_ssl_context()
        with urllib.request.urlopen(request, **open_kwargs) as response:
            record["response"] = {"status": response.status, "reason": response.reason, "headers": dict(response.headers.items()), "body": None}
            buffer = ""
            for chunk in response:
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    event = parse_sse_block(block)
                    if event:
                        record["events"].append(event)
                        collect_event_summary(record, event)
            event = parse_sse_block(buffer)
            if event:
                record["events"].append(event)
                collect_event_summary(record, event)
            finalize_record(record)
    except Exception as exc:
        record["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        if hasattr(exc, "code"):
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""
            record["response"] = {"status": exc.code, "reason": getattr(exc, "reason", ""), "headers": {}, "body": error_body}
    finally:
        record["endedAt"] = display_timestamp(now_local())
    return record


def call_dify_with_curl(record, url, headers, body):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=True) as body_file:
        json.dump(body, body_file, ensure_ascii=False, separators=(",", ":"))
        body_file.flush()
        command = [
            "curl",
            "-sS",
            "-N",
            "--max-time",
            "300",
            "-X",
            "POST",
            url,
            "-H",
            f"Authorization: {headers['Authorization']}",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            f"@{body_file.name}",
            "-w",
            "\n__DIFY_HTTP_STATUS__:%{http_code}\n",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=330, check=False)
        except Exception as exc:
            record["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
            return
    collect_curl_response(record, completed.stdout, completed.stderr)
    if completed.returncode != 0 and record.get("error") is None:
        record["error"] = {"type": "CurlError", "message": completed.stderr.strip() or f"curl exited with {completed.returncode}"}


def extract_final_plan(answer):
    if not answer:
        return None, "answer 为空"
    start_tag = "<FINAL_PLAN_JSON>"
    end_tag = "</FINAL_PLAN_JSON>"
    start = answer.find(start_tag)
    end = answer.find(end_tag, start + len(start_tag))
    candidates = []
    if start >= 0 and end >= 0:
        candidates.append(answer[start + len(start_tag):end].strip())
    candidates.append(answer.strip())
    json_match = re.search(r"\{.*\}", answer, flags=re.S)
    if json_match:
        candidates.append(json_match.group(0))
    errors = []
    for text in candidates:
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("finalPlanJson"), dict):
            return parsed["finalPlanJson"], None
        if isinstance(parsed, dict) and isinstance(parsed.get("finalPlan"), dict):
            return parsed["finalPlan"], None
        if isinstance(parsed, dict) and isinstance(parsed.get("groups"), list):
            return parsed, None
    return None, "最终 JSON 解析失败：" + ("；".join(errors[:2]) if errors else "未找到可用 JSON")


def validate_final_plan(plan):
    allowed_importance = {"重点执行", "常规建议", "补充建议"}
    summary = {
        "errors": [],
        "groupsCount": 0,
        "itemsCount": 0,
        "importantItemsCount": 0,
        "coverageWarnings": [],
    }
    if not isinstance(plan, dict):
        summary["errors"].append("finalPlan 必须是对象")
        return summary
    groups = plan.get("groups")
    if not isinstance(groups, list) or not groups:
        summary["errors"].append("groups 必须是非空数组")
        return summary
    summary["groupsCount"] = len(groups)
    all_text_parts = [
        str(plan.get("planTitle", "")),
        str(plan.get("planSummary", "")),
        str(plan.get("executionPoints", "")),
    ]
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            summary["errors"].append(f"groups[{group_index}] 必须是对象")
            continue
        if group.get("groupType") != "adviceList":
            summary["errors"].append(f"groups[{group_index}].groupType 应为 adviceList")
        if not group.get("groupTitle"):
            summary["errors"].append(f"groups[{group_index}].groupTitle 不能为空")
        items = group.get("items")
        if not isinstance(items, list) or not items:
            summary["errors"].append(f"groups[{group_index}].items 必须是非空数组")
            continue
        all_text_parts.extend([str(group.get("groupTitle", "")), str(group.get("groupSummary", ""))])
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                summary["errors"].append(f"groups[{group_index}].items[{item_index}] 必须是对象")
                continue
            summary["itemsCount"] += 1
            if not item.get("content"):
                summary["errors"].append(f"groups[{group_index}].items[{item_index}].content 不能为空")
            if not item.get("focusPoint"):
                summary["errors"].append(f"groups[{group_index}].items[{item_index}].focusPoint 不能为空")
            importance = item.get("importance")
            if importance not in allowed_importance:
                summary["errors"].append(f"groups[{group_index}].items[{item_index}].importance 非法")
            if importance == "重点执行":
                summary["importantItemsCount"] += 1
            all_text_parts.extend([
                str(item.get("title", "")),
                str(item.get("content", "")),
                str(item.get("focusPoint", "")),
            ])
    all_text = " ".join(all_text_parts)
    coverage_checks = [
        ("有氧运动", ("有氧", "快走", "慢走", "骑行", "游泳")),
        ("抗阻/力量训练", ("抗阻", "力量", "弹力带", "深蹲", "肌力")),
        ("碎片化执行", ("碎片", "分段", "拆成", "夜班", "忙碌")),
        ("运动安全/停止条件", ("停止运动", "低血糖", "胸闷", "胸痛", "头晕", "不适")),
    ]
    for label, keywords in coverage_checks:
        if not any(keyword in all_text for keyword in keywords):
            summary["coverageWarnings"].append(f"未明显覆盖：{label}")
    return summary


def find_message_id(record):
    if record.get("messageId"):
        return str(record["messageId"])
    for event in record.get("events", []):
        payload = event.get("payload")
        if isinstance(payload, dict) and payload.get("message_id"):
            return str(payload["message_id"])
    return "no-messageid"


def write_result_record(case_dir, record, call_time=None, env_name=None):
    case_dir = Path(case_dir)
    call_time = call_time or now_local()
    record_env = record.get("environment") if isinstance(record.get("environment"), dict) else {}
    env_name = normalize_env_name(env_name or record_env.get("name") or DEFAULT_ENV_NAME)
    api_base = record_env.get("apiBase") or (record.get("request") or {}).get("url", "").split("/chat-messages")[0]
    record["environment"] = {"name": env_name, "apiBase": api_base}
    message_id = sanitize_path_part(find_message_id(record), "no-messageid")
    stamp = compact_timestamp(call_time)
    output_prefix = f"{stamp}_{env_name}_{message_id}"
    output_dir = case_dir / output_prefix
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"{output_prefix}_raw-result.json"
    html_path = output_dir / f"{output_prefix}_result.html"
    events_path = output_dir / f"{output_prefix}_events.ndjson"
    write_json_file(raw_path, record)
    if record.get("events"):
        events_path.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in record["events"]) + "\n", encoding="utf-8")
    html_path.write_text(render_html(case_dir, record, message_id), encoding="utf-8")
    return output_dir, raw_path, html_path


def get_run_error_hint(record):
    response = record.get("response") if isinstance(record.get("response"), dict) else {}
    body = response.get("body") or ""
    if response.get("status") == 401 or "Access token is invalid" in str(body):
        return "API Key 无效。请设置环境变量 DIFY_API_KEY，或运行时用 --api-key 传入正确 Key。"
    return ""


def escape(value):
    return html.escape(json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value)


def status_class(value):
    text = str(value or "")
    if "失败" in text or "异常" in text or "error" in text.lower():
        return "bad"
    if "成功" in text or text == "200" or text == "succeeded":
        return "good"
    return "warn"


def format_duration(seconds):
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return "-"
    if value >= 60:
        return f"{value / 60:.1f} 分钟"
    return f"{value:.2f} 秒"


def finished_nodes(record):
    return [node for node in record.get("nodeRuns", []) if node.get("status") and node.get("status") != "running"]


def render_node_rows(record):
    rows = []
    for node in finished_nodes(record):
        rows.append(
            "<tr>"
            f"<td>{escape(str(node.get('title', '')))}</td>"
            f"<td>{escape(str(node.get('type', '')))}</td>"
            f"<td><span class=\"pill {status_class(node.get('status'))}\">{escape(str(node.get('status', '')))}</span></td>"
            f"<td>{escape(format_duration(node.get('elapsedSeconds')))}</td>"
            "</tr>"
        )
    if not rows:
        return "<p class=\"empty\">没有节点运行记录。</p>"
    return "<table><thead><tr><th>节点</th><th>类型</th><th>状态</th><th>耗时</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def render_groups(final_plan):
    groups = final_plan.get("groups") if isinstance(final_plan, dict) else []
    if not isinstance(groups, list) or not groups:
        return "<p class=\"empty\">没有方案分组。</p>"
    cards = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        items = group.get("items") if isinstance(group.get("items"), list) else []
        cards.append(
            "<article class=\"group-card\">"
            f"<h3>{escape(str(group.get('groupTitle', '')))}</h3>"
            f"<p>{escape(str(group.get('groupSummary', '')))}</p>"
            f"<span class=\"meta\">{escape(str(group.get('groupType', '')))} · {len(items)} items</span>"
            "</article>"
        )
    return "<div class=\"group-grid\">" + "".join(cards) + "</div>"


def render_validation(summary):
    if not isinstance(summary, dict):
        return "<p class=\"empty\">没有校验摘要。</p>"
    parts = [
        f"<p>方案分组：<strong>{escape(str(summary.get('groupsCount', 0)))}</strong></p>",
        f"<p>建议条目：<strong>{escape(str(summary.get('itemsCount', 0)))}</strong></p>",
        f"<p>重点执行条目：<strong>{escape(str(summary.get('importantItemsCount', 0)))}</strong></p>",
    ]
    if summary.get("errors"):
        parts.append("<h3>结构问题</h3><pre>" + escape(summary["errors"]) + "</pre>")
    if summary.get("coverageWarnings"):
        parts.append("<h3>覆盖提醒</h3><pre>" + escape(summary["coverageWarnings"]) + "</pre>")
    return "".join(parts)


def parsed_input_value(case_record, key, default=None):
    inputs = ((case_record.get("dify_payload") or {}).get("inputs") or {})
    return parse_maybe_json(inputs.get(key, default))


def list_count(value):
    return len(value) if isinstance(value, list) else 0


def dict_has_content(value):
    if not isinstance(value, dict):
        return False
    return any(item not in (None, "", [], {}) for item in value.values())


def render_metric_cards(cards):
    return "<div class=\"metric-grid\">" + "".join(
        f"<article class=\"metric-card{' text-metric' if len(str(value)) > 8 else ''}\">"
        f"<span>{escape(str(label))}</span>"
        f"<strong>{escape(str(value))}</strong>"
        f"<em>{escape(str(note))}</em>"
        "</article>"
        for label, value, note in cards
    ) + "</div>"


def compact_cell(value):
    if isinstance(value, (dict, list)):
        return "<code>" + escape(json.dumps(value, ensure_ascii=False, separators=(",", ":"))) + "</code>"
    if value in (None, ""):
        return "-"
    return escape(str(value))


def render_structured_table(value):
    if value in (None, "", [], {}):
        return "<p class=\"empty\">没有结构化数据。</p>"
    if isinstance(value, list):
        if not value:
            return "<p class=\"empty\">没有记录。</p>"
        if all(isinstance(item, dict) for item in value):
            columns = []
            for item in value:
                for key in item.keys():
                    if key not in columns:
                        columns.append(key)
            head = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
            rows = []
            for item in value:
                rows.append("<tr>" + "".join(f"<td>{compact_cell(item.get(column))}</td>" for column in columns) + "</tr>")
            return "<div class=\"table-scroll\"><table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
        rows = "".join(f"<tr><td>{index}</td><td>{compact_cell(item)}</td></tr>" for index, item in enumerate(value, 1))
        return "<table><thead><tr><th>#</th><th>值</th></tr></thead><tbody>" + rows + "</tbody></table>"
    if isinstance(value, dict):
        rows = "".join(
            f"<tr><td>{escape(str(key))}</td><td>{compact_cell(item)}</td></tr>"
            for key, item in value.items()
        )
        return "<table><thead><tr><th>字段</th><th>值</th></tr></thead><tbody>" + rows + "</tbody></table>"
    return "<table><tbody><tr><td>值</td><td>" + compact_cell(value) + "</td></tr></tbody></table>"


def render_input_detail(label, value, detail_title, detail_value):
    return (
        "<details class=\"input-detail\">"
        "<summary>"
        f"<span>{escape(str(label))}</span>"
        f"<strong>{escape(str(value if value not in (None, '') else '-'))}</strong>"
        "</summary>"
        f"<h4>{escape(str(detail_title))}</h4>"
        f"{render_structured_table(detail_value)}"
        "</details>"
    )


def build_input_quality(case_record):
    inputs = ((case_record.get("dify_payload") or {}).get("inputs") or {})
    basic = parsed_input_value(case_record, "basicProfile", {})
    disease = parsed_input_value(case_record, "diseaseProfile", {})
    followups = parsed_input_value(case_record, "followupRecordsLast1y", [])
    metrics = parsed_input_value(case_record, "metricRecordsLast1y", [])
    diets = parsed_input_value(case_record, "dietRecordsLast1y", [])
    exercises = parsed_input_value(case_record, "exerciseRecordsLast1y", [])
    meds = parsed_input_value(case_record, "medPickupRecords1y", [])
    goals = parsed_input_value(case_record, "activeControlGoals", [])

    demographics = basic.get("demographics", {}) if isinstance(basic, dict) else {}
    health_info = basic.get("healthInfo", {}) if isinstance(basic, dict) else {}
    lifestyle = basic.get("lifestyle", {}) if isinstance(basic, dict) else {}
    diseases = health_info.get("currentDiseases", []) if isinstance(health_info, dict) else []
    disease_names = []
    for item in diseases if isinstance(diseases, list) else []:
        if isinstance(item, dict):
            disease_names.append(str(item.get("name") or item.get("category") or ""))
        elif item:
            disease_names.append(str(item))

    present_sections = [
        name
        for name, value in (
            ("基础档案", basic),
            ("慢病专项", disease),
            ("随访记录", followups),
            ("指标记录", metrics),
            ("饮食记录", diets),
            ("运动记录", exercises),
            ("用药记录", meds),
            ("控制目标", goals),
        )
        if dict_has_content(value) or list_count(value) > 0
    ]
    missing = []
    if not demographics.get("gender"):
        missing.append("性别")
    if not demographics.get("age"):
        missing.append("年龄")
    if not disease_names:
        missing.append("当前疾病")
    if list_count(metrics) == 0:
        missing.append("近一年指标记录")
    if list_count(exercises) == 0:
        missing.append("近一年运动记录")
    if "height" not in json.dumps(basic, ensure_ascii=False) and "身高" not in json.dumps(basic, ensure_ascii=False):
        missing.append("身高")
    for keyword in ("BMI", "血压", "血糖", "运动禁忌", "并发症", "肾功能", "肌酐", "心血管"):
        if keyword not in json.dumps(inputs, ensure_ascii=False):
            missing.append(keyword)

    return {
        "basic": basic,
        "disease": disease,
        "presentSections": present_sections,
        "missing": missing,
        "counts": {
            "随访记录": list_count(followups),
            "指标记录": list_count(metrics),
            "饮食记录": list_count(diets),
            "运动记录": list_count(exercises),
            "用药记录": list_count(meds),
            "控制目标": list_count(goals),
        },
        "patientFacts": {
            "性别": demographics.get("gender", ""),
            "年龄": demographics.get("age", ""),
            "当前疾病": "、".join(filter(None, disease_names)),
            "生活方式字段": "有" if isinstance(lifestyle, dict) and dict_has_content(lifestyle) else "无",
        },
        "details": {
            "性别": demographics,
            "年龄": demographics,
            "当前疾病": diseases,
            "生活方式字段": lifestyle,
            "运动方式": lifestyle.get("exerciseMethods", {}) if isinstance(lifestyle, dict) else {},
            "随访记录": followups,
            "指标记录": metrics,
            "饮食记录": diets,
            "运动记录": exercises,
            "用药记录": meds,
            "控制目标": goals,
        },
    }


def render_input_quality(case_record):
    quality = build_input_quality(case_record)
    missing = "、".join(quality["missing"]) if quality["missing"] else "未发现明显缺失项"
    cards = [
        ("有效信息模块", len(quality["presentSections"]), "已提供给 AI 的信息类别"),
        ("缺失提醒", missing, "影响个性化程度的关键空项"),
        ("指标记录", quality["counts"]["指标记录"], "近一年 metrics"),
        ("运动记录", quality["counts"]["运动记录"], "近一年 exercise records"),
        ("用药记录", quality["counts"]["用药记录"], "近一年 meds"),
        ("控制目标", quality["counts"]["控制目标"], "active goals"),
    ]
    overview_items = []
    for key, value in quality["patientFacts"].items():
        overview_items.append(render_input_detail(key, value or "-", f"{key}明细", quality["details"].get(key)))
    overview_items.append(render_input_detail("运动方式", "有" if quality["details"].get("运动方式") else "-", "运动方式明细", quality["details"].get("运动方式")))
    for key, value in quality["counts"].items():
        overview_items.append(render_input_detail(key, value, f"{key}明细", quality["details"].get(key)))
    disease_text = escape(quality["disease"]) if quality["disease"] else "<p class=\"empty\">未提供慢病专项信息。</p>"
    return (
        "<section class=\"panel\" id=\"input-quality\"><div class=\"section-head\">"
        "<div><p class=\"eyebrow\">INPUT</p><h2>输入充分性</h2></div>"
        "<p>用于判断 AI 实际拿到了哪些有效信息，以及哪些关键上下文缺失。</p></div>"
        f"{render_metric_cards(cards)}"
        "<div class=\"two-col\">"
        "<article><h3>有效信息概览</h3>"
        f"<div class=\"input-detail-list\">{''.join(overview_items)}</div></article>"
        "<article><h3>慢病专项信息</h3>"
        f"<pre>{disease_text}</pre></article>"
        "</div>"
        "<details><summary>完整入参</summary>"
        f"<pre>{escape((case_record.get('dify_payload') or {}).get('inputs') or {})}</pre>"
        "</details></section>"
    )


def render_plan_groups_detail(final_plan):
    groups = final_plan.get("groups") if isinstance(final_plan, dict) else []
    if not isinstance(groups, list) or not groups:
        return "<p class=\"empty\">没有方案分组。</p>"
    blocks = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        items = group.get("items") if isinstance(group.get("items"), list) else []
        item_rows = []
        for item in items[:6]:
            if not isinstance(item, dict):
                continue
            label = item.get("title") or item.get("day") or item.get("itemType") or "条目"
            item_rows.append(
                "<li>"
                f"<strong>{escape(str(label))}</strong>"
                f"<p class=\"meta\">重要性：{escape(str(item.get('importance', '')))}</p>"
                f"<p>{escape(str(item.get('content', '')))}</p>"
                f"<p class=\"meta\">{escape(str(item.get('focusPoint', '')))}</p>"
                "</li>"
            )
        more = f"<p class=\"meta\">还有 {len(items) - 6} 条未展开。</p>" if len(items) > 6 else ""
        blocks.append(
            "<details class=\"group-detail\" open>"
            "<summary>"
            f"<span><strong>{escape(str(group.get('groupTitle', '')))}</strong><em>{escape(str(group.get('groupType', '')))} · {len(items)} items</em></span>"
            "</summary>"
            f"<p>{escape(str(group.get('groupSummary', '')))}</p>"
            f"<ul class=\"quality-list\">{''.join(item_rows)}</ul>{more}"
            "</details>"
        )
    return "".join(blocks)


def render_sport_completeness(summary):
    errors = (summary or {}).get("errors") or []
    warnings = (summary or {}).get("coverageWarnings") or []
    status_html = "<p class=\"pill good\">运动建议完整性未发现结构问题</p>" if not errors else "<pre>" + escape(errors) + "</pre>"
    warning_html = "<p class=\"pill good\">关键运动维度覆盖较完整</p>" if not warnings else "<pre>" + escape(warnings) + "</pre>"
    return (
        "<h3>运动建议完整性</h3>"
        f"{status_html}"
        "<h3>安全提醒覆盖</h3>"
        f"{warning_html}"
    )


def render_output_quality(final_plan, summary):
    groups = final_plan.get("groups") if isinstance(final_plan, dict) and isinstance(final_plan.get("groups"), list) else []
    summary = summary or {}
    cards = [
        ("方案分组", len(groups), "groups 数量"),
        ("建议条目", summary.get("itemsCount", 0), "items 数量"),
        ("重点执行", summary.get("importantItemsCount", 0), "importance=重点执行"),
        ("结构问题", len(summary.get("errors") or []), "字段完整性"),
        ("覆盖提醒", len(summary.get("coverageWarnings") or []), "有氧/抗阻/碎片/安全"),
    ]
    output_note = "已生成运动建议分组" if groups else "未生成运动建议分组"
    return (
        "<section class=\"panel\" id=\"output-quality\"><div class=\"section-head\">"
        "<div><p class=\"eyebrow\">OUTPUT</p><h2>干预方案产出质量</h2></div>"
        f"<p>{escape(output_note)}</p></div>"
        f"{render_metric_cards(cards)}"
        "<h3>分组内容质检</h3>"
        f"{render_plan_groups_detail(final_plan)}"
        f"{render_sport_completeness(summary)}"
        "<h3>完整性校验摘要</h3>"
        f"{render_validation(summary)}"
        "</section>"
    )


def render_slow_nodes(record):
    nodes = sorted(
        finished_nodes(record),
        key=lambda node: float(node.get("elapsedSeconds") or 0),
        reverse=True,
    )[:5]
    if not nodes:
        return "<p class=\"empty\">没有可排序的节点耗时。</p>"
    rows = []
    max_elapsed = max((float(node.get("elapsedSeconds") or 0) for node in nodes), default=1) or 1
    for node in nodes:
        elapsed = float(node.get("elapsedSeconds") or 0)
        width = max(3, elapsed / max_elapsed * 100)
        rows.append(
            "<article class=\"slow-node\">"
            f"<div><strong>{escape(str(node.get('title', '')))}</strong><span>{escape(format_duration(elapsed))}</span></div>"
            f"<div class=\"bar\"><i style=\"width:{width:.1f}%\"></i></div>"
            "</article>"
        )
    return "".join(rows)


def render_runtime_quality(record):
    metadata = record.get("messageEndMetadata") if isinstance(record.get("messageEndMetadata"), dict) else {}
    usage = metadata.get("usage") if isinstance(metadata.get("usage"), dict) else {}
    nodes = finished_nodes(record)
    total_elapsed = sum(float(node.get("elapsedSeconds") or 0) for node in nodes)
    failed_nodes = [node for node in nodes if str(node.get("status", "")).lower() not in ("succeeded", "success")]
    cards = [
        ("节点数", len(nodes), "已完成节点"),
        ("失败节点", len(failed_nodes), "非 succeeded 状态"),
        ("节点累计耗时", format_duration(total_elapsed), "按 node_finished 汇总"),
        ("Token", usage.get("total_tokens", "-"), "Dify metadata"),
        ("费用", usage.get("total_price", "-"), usage.get("currency", "")),
    ]
    failed_html = "<p class=\"pill good\">没有失败节点</p>" if not failed_nodes else "<pre>" + escape(failed_nodes) + "</pre>"
    return (
        "<section class=\"panel\" id=\"runtime-quality\"><div class=\"section-head\">"
        "<div><p class=\"eyebrow\">RUNTIME</p><h2>节点耗时</h2></div>"
        "<p>用于定位慢节点、失败节点和整体运行成本。</p></div>"
        f"{render_metric_cards(cards)}"
        "<h3>慢节点 Top 5</h3>"
        f"{render_slow_nodes(record)}"
        "<h3>失败节点</h3>"
        f"{failed_html}"
        "<h3>完整节点耗时</h3>"
        f"{render_node_rows(record)}"
        "</section>"
    )


def render_html(case_dir, record, message_id):
    case_record = {}
    try:
        case_record = read_json_file(Path(case_dir) / INPUT_FILE_NAME)
    except Exception:
        pass
    metadata = record.get("caseMetadata") or case_record.get("metadata") or {}
    environment = record.get("environment") if isinstance(record.get("environment"), dict) else {}
    env_name = environment.get("name") or metadata.get("defaultEnvironment") or DEFAULT_ENV_NAME
    env_api_base = environment.get("apiBase") or ((record.get("request") or {}).get("url", "").split("/chat-messages")[0])
    final_plan = record.get("finalPlan") or {}
    summary = record.get("validationSummary") or {}
    error = record.get("error")
    hint = get_run_error_hint(record)
    title = final_plan.get("planTitle") if isinstance(final_plan, dict) else ""
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{escape(str(metadata.get('patientName', '未知患者')))} · 运动方案测试结果</title>
<style>
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:#f4f6f8; color:#17202a; }}
header {{ padding:28px 36px; background:#19313a; color:white; }}
.page-shell {{ display:grid; grid-template-columns:220px minmax(0,1fr); gap:18px; padding:24px 36px 48px; max-width:1480px; margin:0 auto; align-items:start; }}
.quick-nav {{ position:sticky; top:16px; background:white; border:1px solid #dce3ea; border-radius:8px; padding:14px; }}
.quick-nav strong {{ display:block; margin-bottom:10px; font-size:14px; }}
.quick-nav a {{ display:block; color:#294f5a; text-decoration:none; padding:8px 10px; border-radius:6px; font-size:14px; }}
.quick-nav a:hover {{ background:#eef5f7; }}
main {{ min-width:0; }}
.panel {{ background:white; border:1px solid #dce3ea; border-radius:8px; padding:20px; margin:0 0 18px; }}
.section-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:24px; border-bottom:1px solid #edf1f5; padding-bottom:12px; margin-bottom:16px; }}
.section-head h2 {{ margin:2px 0 0; font-size:22px; }}
.section-head p {{ margin:0; max-width:520px; color:#5d6b78; }}
.eyebrow {{ margin:0; color:#657889; font-size:12px; font-weight:700; letter-spacing:0; }}
.meta {{ color:#607080; font-size:13px; }}
.pill {{ display:inline-block; padding:3px 8px; border-radius:999px; background:#eef2f4; font-size:12px; }}
.good {{ background:#e1f7ea; color:#0d6b3f; }} .bad {{ background:#ffe3e3; color:#a12525; }} .warn {{ background:#fff2cc; color:#7a5300; }}
table {{ width:100%; border-collapse:collapse; }} th,td {{ border-bottom:1px solid #e6ebf0; padding:9px 10px; text-align:left; vertical-align:top; }}
pre {{ white-space:pre-wrap; overflow:auto; background:#0f1720; color:#e8edf2; padding:14px; border-radius:6px; }}
.metric-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:14px 0 18px; }}
.metric-card {{ border:1px solid #dfe6ed; background:#fbfcfd; border-radius:8px; padding:13px; min-height:82px; }}
.metric-card span,.metric-card em {{ display:block; color:#657383; font-size:12px; font-style:normal; }}
.metric-card strong {{ display:block; margin:6px 0; font-size:26px; line-height:1; }}
.metric-card.text-metric strong {{ font-size:15px; line-height:1.45; word-break:break-word; }}
.two-col {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:16px; }}
.group-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; }}
.group-card,.group-detail {{ border:1px solid #e0e6ed; border-radius:8px; padding:14px; margin-bottom:10px; }}
.group-detail summary {{ cursor:pointer; list-style:none; }}
.group-detail summary span {{ display:flex; justify-content:space-between; gap:16px; }}
.group-detail em {{ color:#657383; font-style:normal; font-size:13px; }}
.quality-list {{ margin:10px 0 0; padding-left:18px; }}
.quality-list li {{ margin-bottom:10px; }}
.input-detail {{ border:1px solid #e0e6ed; border-radius:8px; margin-bottom:8px; overflow:hidden; }}
.input-detail summary {{ display:grid; grid-template-columns:minmax(120px,1fr) auto; gap:12px; align-items:center; cursor:pointer; padding:10px 12px; background:#fbfcfd; }}
.input-detail summary strong {{ font-size:14px; }}
.input-detail h4 {{ margin:12px 12px 6px; }}
.input-detail table,.input-detail .empty {{ margin:0 12px 12px; }}
.table-scroll {{ overflow:auto; margin:0 12px 12px; }}
.input-detail code {{ white-space:normal; word-break:break-all; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:#2d4652; }}
.slow-node {{ border:1px solid #e0e6ed; border-radius:8px; padding:10px 12px; margin-bottom:8px; }}
.slow-node div:first-child {{ display:flex; justify-content:space-between; gap:12px; }}
.bar {{ height:8px; background:#edf2f6; border-radius:999px; overflow:hidden; margin-top:8px; }}
.bar i {{ display:block; height:100%; background:#2b6975; }}
.raw-details > summary {{ cursor:pointer; display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.raw-details > summary h2 {{ margin:0; }}
.raw-details > summary span {{ color:#607080; font-size:13px; }}
.empty {{ color:#6b7785; }}
@media (max-width: 900px) {{ .page-shell {{ display:block; padding:16px; }} .quick-nav {{ position:static; margin-bottom:14px; }} .quick-nav a {{ display:inline-block; }} }}
@media (max-width: 760px) {{ .section-head,.two-col {{ display:block; }} }}
</style>
</head>
<body>
<header>
<h1>{escape(str(metadata.get('patientName', '未知患者')))} · AI 工作流质控</h1>
<p>message_id: {escape(str(message_id))} · conversation_id: {escape(str(record.get('conversationId', '')))}</p>
</header>
<div class="page-shell">
<nav class="quick-nav" aria-label="快速定位">
<strong>快速定位</strong>
<a href="#run-overview">运行概览</a>
<a href="#input-quality">输入充分性</a>
<a href="#output-quality">产出质量</a>
<a href="#runtime-quality">节点耗时</a>
<a href="#raw-data">完整原始数据</a>
</nav>
<main>
<section class="panel" id="run-overview"><h2>运行概览</h2>
<p>环境：<strong>{escape(str(env_name))}</strong>；API Base：{escape(str(env_api_base))}</p>
<p>开始：{escape(str(record.get('startedAt', '')))}；结束：{escape(str(record.get('endedAt', '')))}</p>
<p>HTTP 状态：{escape(str((record.get('response') or {}).get('status', '')))}</p>
<p>方案标题：<strong>{escape(str(title))}</strong></p>
{f'<pre>{escape(error)}</pre>' if error else ''}
{f'<p class="pill bad">{escape(hint)}</p>' if hint else ''}
</section>
{render_input_quality(case_record)}
{render_output_quality(final_plan, summary)}
{render_runtime_quality(record)}
<section class="panel" id="raw-data"><details class="raw-details"><summary><h2>完整原始数据</h2><span>点击展开</span></summary><pre>{escape(record)}</pre></details></section>
</main>
</div>
</body>
</html>"""
    return html_text


def command_prepare_input(args):
    result = prepare_input_file(args.input, args.output_root, env_name=args.env_name)
    print(f"入参文件：{result.input_path}")
    print(f"患者名称：{result.patient_name}")
    print("普通终端执行命令：")
    print(result.terminal_command)


def command_run(args):
    api_key = resolve_api_key(args.api_key, args.env_name)
    if not api_key:
        raise RuntimeError(f"缺少 {env_api_key_name(args.env_name)} 或 DIFY_API_KEY。请设置环境变量或使用 --api-key。")
    case_dir, case_record = load_case_input(args.case_dir)
    record = call_dify_chatflow(
        case_record,
        api_base=args.api_base,
        api_key=api_key,
        query=args.query,
        transport=args.transport,
        env_name=args.env_name,
    )
    output_dir, raw_path, html_path = write_result_record(case_dir, record, env_name=args.env_name)
    print(f"结果目录：{output_dir}")
    print(f"原始结果：{raw_path}")
    print(f"HTML结果：{html_path}")
    if record.get("error"):
        print(f"运行错误：{record['error']}")
        hint = get_run_error_hint(record)
        if hint:
            print(hint)


def command_render_html(args):
    raw_path = Path(args.record)
    record = read_json_file(raw_path)
    case_dir = raw_path.parents[1]
    message_id = sanitize_path_part(find_message_id(record), "no-messageid")
    html_path = raw_path.with_name(raw_path.name.replace("_raw-result.json", "_result.html"))
    html_path.write_text(render_html(case_dir, record, message_id), encoding="utf-8")
    print(f"HTML结果：{html_path}")


def build_parser():
    parser = argparse.ArgumentParser(description="AIHcare 运动方案 Dify Chatflow 运行测试工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-input", help="结构化测试入参并生成 case 目录")
    prepare.add_argument("--input", default=str(DEFAULT_SOURCE_FILE), help="原始入参 JSON 路径")
    prepare.add_argument("--output-root", default=None, help="输出根目录，默认 demo/userinput")
    prepare.add_argument("--env-name", default=DEFAULT_ENV_NAME, help="默认环境名，仅写入入参记录和生成命令")
    prepare.set_defaults(func=command_prepare_input)

    run = subparsers.add_parser("run", help="调用 Dify Chatflow 并归档结果")
    run.add_argument("--case-dir", required=True, help="case 目录，绝对路径或相对 demo 的路径")
    run.add_argument("--env-name", default=DEFAULT_ENV_NAME, help="环境名，会进入结果目录、文件名和报告")
    run.add_argument("--api-base", default=DEFAULT_API_BASE)
    run.add_argument("--api-key", default=None)
    run.add_argument("--query", default=DEFAULT_QUERY)
    run.add_argument("--transport", choices=("curl", "urllib"), default="curl")
    run.set_defaults(func=command_run)

    render = subparsers.add_parser("render-html", help="从 raw-result.json 重新渲染 HTML")
    render.add_argument("--record", required=True)
    render.set_defaults(func=command_render_html)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
