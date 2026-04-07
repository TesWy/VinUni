import json
import os
import re
import time
import uuid
from html import escape
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from observability import LOG_FILE, TRACE_FILE, get_logger, set_current_turn_id, write_trace
from response_utils import normalize_response_text, render_message_content
from tools import calculate_budget, convert_currency, get_weather, search_flights, search_hotels

load_dotenv()
LOGGER = get_logger("travelbuddy.streamlit")
TOOLS_LIST = [search_flights, search_hotels, calculate_budget, get_weather, convert_currency]
BASE_DIR = Path(__file__).resolve().parent
CHAT_STORE_FILE = BASE_DIR / "logs" / "chat_sessions.json"
TOOL_LABELS = {
    "search_flights": "Search flights",
    "search_hotels": "Search hotels",
    "calculate_budget": "Calculate budget",
    "get_weather": "Check weather",
    "convert_currency": "Convert currency",
}
STEP_REWRITES = {
    "Reviewing your request": "Understanding your travel request",
    "Planning the next action": "Choosing the next action",
    "Collecting data from tools": "Collecting data from tools",
    "Preparing the final answer": "Writing the final answer",
}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def format_tool_label(tool_name: str) -> str:
    return TOOL_LABELS.get(tool_name, tool_name.replace("_", " ").title())


def to_relative_display(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def render_path_card(title: str, path: Path) -> None:
    relative_path = to_relative_display(path)
    absolute_path = str(path)
    st.markdown(
        f"""
        <div class="path-card">
            <div class="path-card-title">{title}</div>
            <div class="path-card-path">{relative_path}</div>
            <div class="path-card-sub">Absolute: {absolute_path}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_text(text: str, role: str) -> None:
    css_class = "assistant-bubble" if role == "assistant" else "user-bubble"
    shell_class = "assistant-shell" if role == "assistant" else "user-shell"
    sender = "TravelBuddy" if role == "assistant" else "You"
    display_text = normalize_response_text(text) if role == "assistant" else str(text)
    safe_html = escape(display_text).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="message-shell {shell_class}">
            <div class="message-label">{sender}</div>
            <div class="{css_class}">
                {safe_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sanitize_step_text(step: str) -> str:
    text = str(step or "")
    text = text.replace("```html", "").replace("```", "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    text = " ".join(text.split()).strip(" -")
    return STEP_REWRITES.get(text, text)


def normalize_steps(steps: list[str]) -> list[str]:
    cleaned = []
    for raw_step in steps:
        text = sanitize_step_text(raw_step)
        if not text:
            continue
        if cleaned and cleaned[-1] == text:
            continue
        cleaned.append(text)
    return cleaned[-6:]


def build_steps_html(steps: list[str], pending: bool = False) -> str:
    normalized_steps = normalize_steps(steps)
    title = "TravelBuddy is working" if pending else "Execution timeline"
    subtitle = "Live progress" if pending else "What happened behind the scenes"
    status_label = "LIVE" if pending else "DONE"
    items = []
    for idx, step in enumerate(normalized_steps, start=1):
        row_class = "step-item current-step" if pending and idx == len(normalized_steps) else "step-item"
        items.append(
            (
                f'<div class="{row_class}">'
                f'<div class="step-index">{idx}</div>'
                f'<div class="step-text">{escape(step)}</div>'
                "</div>"
            )
        )
    if not items:
        items.append(
            '<div class="step-item current-step">'
            '<div class="step-index">1</div>'
            '<div class="step-text">Starting up...</div>'
            "</div>"
        )
    items_html = "".join(items)
    card_class = "steps-card pending-card" if pending else "steps-card"
    return (
        f'<div class="{card_class}">'
        '<div class="steps-head">'
        '<div>'
        f'<div class="steps-title">{title}</div>'
        f'<div class="steps-subtitle">{subtitle}</div>'
        "</div>"
        f'<div class="steps-badge">{status_label}</div>'
        "</div>"
        f'<div class="steps-list">{items_html}</div>'
        "</div>"
    )


def render_steps_panel(placeholder, steps: list[str], pending: bool = False) -> None:
    placeholder.markdown(build_steps_html(steps, pending=pending), unsafe_allow_html=True)


def load_system_prompt() -> str:
    prompt_path = BASE_DIR / "system_prompt.txt"
    if not prompt_path.exists():
        return "You are TravelBuddy, a helpful travel planning assistant."
    return prompt_path.read_text(encoding="utf-8")


def build_llm(provider: str, model: str):
    if provider == "openai":
        return ChatOpenAI(model=model)
    return ChatGoogleGenerativeAI(model=model)


@st.cache_resource
def get_graph(provider: str, model: str, system_prompt: str):
    llm = build_llm(provider, model)
    llm_with_tools = llm.bind_tools(TOOLS_LIST)

    def agent_node(state: AgentState, config: RunnableConfig):
        turn_id = config.get("configurable", {}).get("turn_id", "unknown")
        pane = config.get("configurable", {}).get("pane", "single")
        set_current_turn_id(turn_id)

        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages

        LOGGER.info(
            "streamlit agent_node start | turn_id=%s | pane=%s | provider=%s | model=%s | message_count=%s",
            turn_id,
            pane,
            provider,
            model,
            len(messages),
        )
        response = llm_with_tools.invoke(messages)
        text_output = render_message_content(getattr(response, "content", ""))

        write_trace(
            "ui.model.response",
            {
                "pane": pane,
                "provider": provider,
                "model": model,
                "has_tool_calls": bool(response.tool_calls),
                "tool_call_count": len(response.tool_calls) if response.tool_calls else 0,
                "content_preview": text_output[:300],
                "raw_content": response.content,
            },
            turn_id=turn_id,
        )
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS_LIST))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()


def parse_logs() -> pd.DataFrame:
    if not LOG_FILE.exists():
        return pd.DataFrame(columns=["timestamp", "level", "logger", "message"])

    pattern = re.compile(r"^(.*?) \| (\w+) \| ([^|]+) \| (.*)$")
    rows = []
    for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        ts, level, logger_name, message = m.groups()
        rows.append(
            {
                "timestamp": ts,
                "level": level,
                "logger": logger_name.strip(),
                "message": message.strip(),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def parse_traces() -> pd.DataFrame:
    if not TRACE_FILE.exists():
        return pd.DataFrame(columns=["timestamp_utc", "turn_id", "event", "payload"])

    rows = []
    for line in TRACE_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            rows.append(obj)
        except json.JSONDecodeError:
            continue
    df = pd.DataFrame(rows)
    if not df.empty and "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], errors="coerce", utc=True)
    return df


def ensure_state() -> None:
    if "chat_store" not in st.session_state:
        st.session_state.chat_store = load_chat_store()
    if "single_messages" not in st.session_state:
        st.session_state.single_messages = []
    if "left_messages" not in st.session_state:
        st.session_state.left_messages = []
    if "right_messages" not in st.session_state:
        st.session_state.right_messages = []
    if "single_session_id" not in st.session_state:
        st.session_state.single_session_id = ensure_session("single")
        st.session_state.single_messages = get_session_messages("single", st.session_state.single_session_id)
    if "left_session_id" not in st.session_state:
        st.session_state.left_session_id = ensure_session("left")
        st.session_state.left_messages = get_session_messages("left", st.session_state.left_session_id)
    if "right_session_id" not in st.session_state:
        st.session_state.right_session_id = ensure_session("right")
        st.session_state.right_messages = get_session_messages("right", st.session_state.right_session_id)


def load_chat_store() -> dict:
    if not CHAT_STORE_FILE.exists():
        return {"single": {}, "left": {}, "right": {}}
    try:
        data = json.loads(CHAT_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"single": {}, "left": {}, "right": {}}
    for pane in ("single", "left", "right"):
        data.setdefault(pane, {})
    return data


def save_chat_store() -> None:
    CHAT_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_STORE_FILE.write_text(
        json.dumps(st.session_state.chat_store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_session(pane: str) -> str:
    session_id = f"{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    st.session_state.chat_store[pane][session_id] = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "title": "New Trip",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
    }
    save_chat_store()
    return session_id


def ensure_session(pane: str) -> str:
    pane_store = st.session_state.chat_store.get(pane, {})
    if pane_store:
        latest = sorted(
            pane_store.items(),
            key=lambda kv: kv[1].get("updated_at", ""),
            reverse=True,
        )[0][0]
        return latest
    return create_session(pane)


def get_session_messages(pane: str, session_id: str) -> list[dict]:
    pane_store = st.session_state.chat_store.get(pane, {})
    return pane_store.get(session_id, {}).get("messages", [])


def save_session_messages(pane: str, session_id: str, messages: list[dict]) -> None:
    pane_store = st.session_state.chat_store.setdefault(pane, {})
    if session_id not in pane_store:
        pane_store[session_id] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": "New Trip",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
        }
    session = pane_store[session_id]
    session["messages"] = messages
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    if messages and session.get("title") in ("", "New Trip"):
        first_user = next((m["content"] for m in messages if m.get("role") == "user"), "New Trip")
        session["title"] = first_user[:50]
    save_chat_store()


def render_session_selector(pane: str, label: str, state_key: str, msg_key: str) -> None:
    pane_store = st.session_state.chat_store.get(pane, {})
    if not pane_store:
        sid = create_session(pane)
        st.session_state[state_key] = sid
        st.session_state[msg_key] = []
        return

    sorted_items = sorted(
        pane_store.items(),
        key=lambda kv: kv[1].get("updated_at", ""),
        reverse=True,
    )
    options = [sid for sid, _ in sorted_items]
    labels = {
        sid: f"{meta.get('date', 'unknown')} | {meta.get('title', 'Chat')}"
        for sid, meta in sorted_items
    }

    if st.session_state.get(state_key) not in options:
        st.session_state[state_key] = options[0]

    selected_sid = st.selectbox(
        label,
        options=options,
        format_func=lambda x: labels.get(x, x),
        key=f"{pane}_session_selector",
        index=options.index(st.session_state[state_key]),
    )
    if selected_sid != st.session_state[state_key]:
        st.session_state[state_key] = selected_sid
        st.session_state[msg_key] = get_session_messages(pane, selected_sid)

    if st.button(f"New {pane.capitalize()} Chat", key=f"new_{pane}_chat"):
        new_sid = create_session(pane)
        st.session_state[state_key] = new_sid
        st.session_state[msg_key] = []
        st.rerun()


def render_chat_history(messages: list[dict]) -> None:
    for msg in messages:
        with st.chat_message(msg["role"]):
            render_chat_text(msg["content"], msg["role"])


def run_agent_turn(
    prompt: str,
    provider: str,
    model: str,
    pane: str,
    history: list[dict],
    on_step=None,
) -> tuple[str, list[str], str]:
    system_prompt = load_system_prompt()
    graph = get_graph(provider, model, system_prompt)
    turn_id = str(uuid.uuid4())
    set_current_turn_id(turn_id)
    started = time.perf_counter()

    write_trace(
        "ui.turn.start",
        {"pane": pane, "provider": provider, "model": model, "user_input": prompt},
        turn_id=turn_id,
    )
    LOGGER.info(
        "ui turn start | turn_id=%s | pane=%s | provider=%s | model=%s",
        turn_id,
        pane,
        provider,
        model,
    )

    graph_messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            graph_messages.append(("human", content))
        elif role == "assistant":
            graph_messages.append(("ai", content))

    step_logs = []

    def push_step(message: str) -> None:
        cleaned_message = sanitize_step_text(message)
        if not cleaned_message:
            return
        if step_logs and step_logs[-1] == cleaned_message:
            return
        step_logs.append(cleaned_message)
        write_trace(
            "ui.turn.step",
            {
                "pane": pane,
                "provider": provider,
                "model": model,
                "message": cleaned_message,
            },
            turn_id=turn_id,
        )
        if on_step is not None:
            on_step(step_logs.copy())

    push_step("Reviewing your request")

    final = None
    try:
        for update in graph.stream(
            {"messages": graph_messages},
            config={"configurable": {"turn_id": turn_id, "pane": pane}},
            stream_mode="updates",
        ):
            if not isinstance(update, dict):
                continue
            for node_name, node_payload in update.items():
                if node_name == "agent":
                    push_step("Planning the next action")
                elif node_name == "tools":
                    push_step("Collecting data from tools")
                else:
                    push_step(f"Completed step: {node_name}")

                if isinstance(node_payload, dict) and "messages" in node_payload and node_payload["messages"]:
                    maybe_last = node_payload["messages"][-1]
                    if hasattr(maybe_last, "tool_calls") and getattr(maybe_last, "tool_calls"):
                        tool_names = [format_tool_label(tc.get("name", "unknown_tool")) for tc in maybe_last.tool_calls]
                        push_step(f"Using tool: {', '.join(tool_names)}")
                    final = maybe_last

        if final is None:
            result = graph.invoke(
                {"messages": graph_messages},
                config={"configurable": {"turn_id": turn_id, "pane": pane}},
            )
            final = result["messages"][-1]
            push_step("Preparing the final answer")
        else:
            push_step("Preparing the final answer")
    except Exception as exc:
        LOGGER.exception(
            "ui turn error | turn_id=%s | pane=%s | provider=%s | model=%s",
            turn_id,
            pane,
            provider,
            model,
        )
        write_trace(
            "ui.turn.error",
            {"pane": pane, "provider": provider, "model": model, "error": str(exc)},
            turn_id=turn_id,
        )
        return f"Loi khi goi model ({provider}:{model}): {exc}", step_logs, turn_id

    answer = render_message_content(getattr(final, "content", ""))
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    write_trace(
        "ui.turn.end",
        {"pane": pane, "provider": provider, "model": model, "elapsed_ms": elapsed_ms, "answer_preview": answer[:400]},
        turn_id=turn_id,
    )
    LOGGER.info(
        "ui turn end | turn_id=%s | pane=%s | provider=%s | model=%s | elapsed_ms=%s",
        turn_id,
        pane,
        provider,
        model,
        elapsed_ms,
    )
    return answer, step_logs, turn_id


def render_travel_header() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at 20% 10%, #e8f7ff 0%, #f6fbff 35%, #fff7ea 100%);
        }
        section[data-testid="stMain"],
        section[data-testid="stMain"] .stMarkdown,
        section[data-testid="stMain"] .stMarkdown p,
        section[data-testid="stMain"] .stMarkdown li,
        section[data-testid="stMain"] .stMarkdown ul,
        section[data-testid="stMain"] .stMarkdown ol,
        section[data-testid="stMain"] .stMarkdown span,
        section[data-testid="stMain"] .stMarkdown strong,
        section[data-testid="stMain"] .stMarkdown em,
        section[data-testid="stMain"] .stChatMessage,
        section[data-testid="stMain"] .stChatMessage p,
        section[data-testid="stMain"] .stChatMessage li,
        section[data-testid="stMain"] .stChatMessage span,
        section[data-testid="stMain"] div[data-testid="stChatMessageContent"],
        section[data-testid="stMain"] div[data-testid="stChatMessageContent"] p,
        section[data-testid="stMain"] div[data-testid="stChatMessageContent"] li,
        section[data-testid="stMain"] div[data-testid="stChatMessageContent"] span,
        section[data-testid="stMain"] div[data-testid="stMarkdownContainer"],
        section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] p,
        section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] li,
        section[data-testid="stMain"] div[data-testid="stMarkdownContainer"] span,
        section[data-testid="stMain"] div[data-testid="stExpander"] *,
        section[data-testid="stMain"] summary,
        section[data-testid="stMain"] summary span,
        section[data-testid="stMain"] label,
        section[data-testid="stMain"] h1,
        section[data-testid="stMain"] h2,
        section[data-testid="stMain"] h3,
        section[data-testid="stMain"] h4 {
            color: #13293d !important;
        }
        section[data-testid="stMain"] div[data-testid="stChatMessageContent"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid #d7e7f4;
            border-radius: 14px;
            padding: 10px 12px;
        }
        section[data-testid="stMain"] div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid #d7e7f4;
            border-radius: 14px;
            overflow: hidden;
        }
        section[data-testid="stMain"] div[data-testid="stExpander"] details summary {
            background: rgba(227, 240, 250, 0.85);
            padding: 6px 10px;
        }
        section[data-testid="stMain"] div[data-testid="stExpanderDetails"] {
            background: rgba(255, 255, 255, 0.72);
        }
        section[data-testid="stMain"] div[data-testid="stSegmentedControl"] button {
            color: #173a60 !important;
            background: rgba(255, 255, 255, 0.72) !important;
            border: 1px solid #bfd7eb !important;
        }
        section[data-testid="stMain"] div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
            color: #ffffff !important;
            background: linear-gradient(135deg, #1476d2, #15967d) !important;
            border-color: transparent !important;
        }
        section[data-testid="stMain"] .stButton > button {
            color: #173a60 !important;
            background: rgba(255, 255, 255, 0.78) !important;
            border: 1px solid #bfd7eb !important;
            border-radius: 12px !important;
        }
        section[data-testid="stMain"] .stButton > button:hover {
            background: #f3fbff !important;
            border-color: #61aee8 !important;
        }
        section[data-testid="stMain"] [data-testid="stMetricValue"] {
            color: #15385d !important;
        }
        .path-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid #d6e7f4;
            border-radius: 16px;
            padding: 14px 16px;
            min-height: 110px;
        }
        .path-card-title {
            color: #5d7693;
            font-size: 0.9rem;
            margin-bottom: 6px;
        }
        .path-card-path {
            color: #16395d;
            font-size: 1rem;
            font-weight: 700;
            word-break: break-word;
        }
        .path-card-sub {
            color: #6f86a1;
            font-size: 0.8rem;
            margin-top: 8px;
            word-break: break-all;
        }
        .assistant-bubble {
            color: #13293d !important;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #d7e7f4;
            border-radius: 14px;
            padding: 12px 14px;
            line-height: 1.6;
            white-space: normal;
        }
        .user-bubble {
            color: #ffffff !important;
            background: linear-gradient(135deg, #1476d2, #15967d);
            border: 1px solid transparent;
            border-radius: 14px;
            padding: 12px 14px;
            line-height: 1.6;
            white-space: normal;
        }
        .assistant-bubble *, .user-bubble * {
            color: inherit !important;
        }
        .message-shell {
            margin: 8px 0 14px;
        }
        .message-label {
            font-size: 0.82rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .assistant-shell .message-label {
            color: #52708f !important;
        }
        .user-shell .message-label {
            color: #3b5f86 !important;
            text-align: right;
        }
        .user-shell .user-bubble {
            margin-left: auto;
            max-width: 78%;
        }
        .assistant-shell .assistant-bubble {
            max-width: 88%;
        }
        .steps-card {
            margin: 10px 0 14px;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #cfe0ef;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(245, 250, 255, 0.88));
            box-shadow: 0 12px 30px rgba(22, 57, 93, 0.08);
        }
        .pending-card {
            background: linear-gradient(135deg, rgba(20, 118, 210, 0.12), rgba(21, 150, 125, 0.12));
            border-color: rgba(108, 171, 217, 0.45);
        }
        .steps-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }
        .steps-title {
            color: #16395d !important;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 3px;
        }
        .steps-subtitle {
            color: #6a829d !important;
            font-size: 0.82rem;
            margin-bottom: 10px;
        }
        .steps-list {
            display: grid;
            gap: 10px;
        }
        .step-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            color: #173a60 !important;
            padding: 10px 12px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid rgba(191, 215, 235, 0.9);
        }
        .current-step {
            border-color: rgba(82, 150, 212, 0.9);
            background: linear-gradient(135deg, rgba(20, 118, 210, 0.10), rgba(21, 150, 125, 0.08));
        }
        .step-index {
            width: 26px;
            height: 26px;
            border-radius: 999px;
            background: linear-gradient(135deg, #1476d2, #15967d);
            color: #ffffff !important;
            font-size: 0.82rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
            box-shadow: 0 6px 14px rgba(20, 118, 210, 0.22);
        }
        .step-text {
            color: #173a60 !important;
            line-height: 1.5;
            padding-top: 1px;
        }
        .steps-badge {
            color: #0e5d67 !important;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(111, 178, 186, 0.7);
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.08em;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #16202f 0%, #20293a 100%);
            border-right: 1px solid rgba(235, 244, 255, 0.08);
        }
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] small {
            color: #eaf3ff !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div {
            background: rgba(10, 16, 24, 0.75) !important;
            border: 1px solid rgba(210, 226, 245, 0.18) !important;
            border-radius: 12px !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        section[data-testid="stSidebar"] [data-baseweb="input"] * {
            color: #f5f9ff !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            color: #f5f9ff !important;
            border: 1px solid rgba(210, 226, 245, 0.22) !important;
            background: rgba(255, 255, 255, 0.04) !important;
            border-radius: 12px !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: rgba(132, 199, 255, 0.65) !important;
            background: rgba(84, 176, 255, 0.14) !important;
        }
        .hero-box {
            border: 1px solid #dce8f5;
            background: linear-gradient(140deg, rgba(26, 115, 232, 0.08), rgba(19, 170, 82, 0.08));
            border-radius: 18px;
            padding: 18px 20px;
            margin-bottom: 14px;
        }
        .hero-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #14375c;
            margin-bottom: 4px;
        }
        .hero-subtitle {
            color: #2a527e;
            font-size: 0.98rem;
        }
        </style>
        <div class="hero-box">
            <div class="hero-title">TravelBuddy Console</div>
            <div class="hero-subtitle">Planner chat + observability dashboard for tools, logs, and traces.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chat_tab() -> None:
    ensure_state()
    st.subheader("Travel Chat")

    mode = st.segmented_control("Mode", options=["Single", "Compare"], default="Single")

    with st.sidebar:
        st.markdown("### Model Setup")
        if mode == "Single":
            render_session_selector("single", "Single Chat Sessions", "single_session_id", "single_messages")
            single_provider = st.selectbox("Provider", ["gemini", "openai"], index=0, key="single_provider")
            default_model = "gemma-4-31b-it" if single_provider == "gemini" else "gpt-4o-mini"
            single_model = st.text_input("Model", value=default_model, key="single_model")
            if st.button("Clear Single Chat"):
                st.session_state.single_messages = []
                save_session_messages("single", st.session_state.single_session_id, st.session_state.single_messages)
                st.rerun()
        else:
            render_session_selector("left", "Left Sessions", "left_session_id", "left_messages")
            render_session_selector("right", "Right Sessions", "right_session_id", "right_messages")
            left_provider = st.selectbox("Left Provider", ["gemini", "openai"], index=0, key="left_provider")
            right_provider = st.selectbox("Right Provider", ["openai", "gemini"], index=0, key="right_provider")
            left_default = "gemma-4-31b-it" if left_provider == "gemini" else "gpt-4o-mini"
            right_default = "gpt-4o-mini" if right_provider == "openai" else "gemma-4-31b-it"
            left_model = st.text_input("Left Model", value=left_default, key="left_model")
            right_model = st.text_input("Right Model", value=right_default, key="right_model")
            if st.button("Clear Compare Chat"):
                st.session_state.left_messages = []
                st.session_state.right_messages = []
                save_session_messages("left", st.session_state.left_session_id, st.session_state.left_messages)
                save_session_messages("right", st.session_state.right_session_id, st.session_state.right_messages)
                st.rerun()

    if mode == "Single":
        render_chat_history(st.session_state.single_messages)
        prompt = st.chat_input("Plan my trip...")
        if prompt:
            st.session_state.single_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                render_chat_text(prompt, "user")
            with st.chat_message("assistant"):
                progress_placeholder = st.empty()
                render_steps_panel(progress_placeholder, ["Reviewing your request"], pending=True)
                with st.spinner("TravelBuddy is planning your trip..."):
                    answer, steps, _turn_id = run_agent_turn(
                        prompt,
                        single_provider,
                        single_model,
                        pane="single",
                        history=st.session_state.single_messages,
                        on_step=lambda current_steps: render_steps_panel(
                            progress_placeholder,
                            current_steps,
                            pending=True,
                        ),
                    )
                progress_placeholder.empty()
                render_chat_text(answer, "assistant")
                if steps:
                    st.markdown(build_steps_html(steps, pending=False), unsafe_allow_html=True)
            st.session_state.single_messages.append({"role": "assistant", "content": answer})
            save_session_messages("single", st.session_state.single_session_id, st.session_state.single_messages)
    else:
        col_left, col_right = st.columns(2, gap="medium")
        with col_left:
            st.markdown(f"#### Left: `{left_provider}:{left_model}`")
            render_chat_history(st.session_state.left_messages)
        with col_right:
            st.markdown(f"#### Right: `{right_provider}:{right_model}`")
            render_chat_history(st.session_state.right_messages)

        prompt = st.chat_input("Ask once, compare both models...")
        if prompt:
            st.session_state.left_messages.append({"role": "user", "content": prompt})
            st.session_state.right_messages.append({"role": "user", "content": prompt})

            with col_left:
                with st.chat_message("user"):
                    render_chat_text(prompt, "user")
                with st.chat_message("assistant"):
                    left_progress_placeholder = st.empty()
                    render_steps_panel(left_progress_placeholder, ["Reviewing your request"], pending=True)
                    with st.spinner("Left model is thinking..."):
                        left_answer, left_steps, _left_turn_id = run_agent_turn(
                            prompt,
                            left_provider,
                            left_model,
                            pane="left",
                            history=st.session_state.left_messages,
                            on_step=lambda current_steps: render_steps_panel(
                                left_progress_placeholder,
                                current_steps,
                                pending=True,
                            ),
                        )
                    left_progress_placeholder.empty()
                    render_chat_text(left_answer, "assistant")
                    if left_steps:
                        st.markdown(build_steps_html(left_steps, pending=False), unsafe_allow_html=True)
                st.session_state.left_messages.append({"role": "assistant", "content": left_answer})
                save_session_messages("left", st.session_state.left_session_id, st.session_state.left_messages)

            with col_right:
                with st.chat_message("user"):
                    render_chat_text(prompt, "user")
                with st.chat_message("assistant"):
                    right_progress_placeholder = st.empty()
                    render_steps_panel(right_progress_placeholder, ["Reviewing your request"], pending=True)
                    with st.spinner("Right model is thinking..."):
                        right_answer, right_steps, _right_turn_id = run_agent_turn(
                            prompt,
                            right_provider,
                            right_model,
                            pane="right",
                            history=st.session_state.right_messages,
                            on_step=lambda current_steps: render_steps_panel(
                                right_progress_placeholder,
                                current_steps,
                                pending=True,
                            ),
                        )
                    right_progress_placeholder.empty()
                    render_chat_text(right_answer, "assistant")
                    if right_steps:
                        st.markdown(build_steps_html(right_steps, pending=False), unsafe_allow_html=True)
                st.session_state.right_messages.append({"role": "assistant", "content": right_answer})
                save_session_messages("right", st.session_state.right_session_id, st.session_state.right_messages)


def observability_tab() -> None:
    st.subheader("Observability")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_path_card("Log File", LOG_FILE)
    with c2:
        render_path_card("Trace File", TRACE_FILE)
    with c3:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("Refresh Data", width="stretch"):
            st.rerun()

    logs_df = parse_logs()
    traces_df = parse_traces()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Log Rows", len(logs_df))
    m2.metric("Trace Rows", len(traces_df))
    m3.metric("Unique Turns", traces_df["turn_id"].nunique() if not traces_df.empty else 0)

    avg_latency = 0
    if not traces_df.empty:
        turn_end = traces_df[traces_df["event"].isin(["turn.end", "ui.turn.end"])]
        if not turn_end.empty:
            elapsed = []
            for payload in turn_end["payload"].tolist():
                if isinstance(payload, dict) and "elapsed_ms" in payload:
                    elapsed.append(payload["elapsed_ms"])
            if elapsed:
                avg_latency = int(sum(elapsed) / len(elapsed))
    m4.metric("Avg Latency (ms)", avg_latency)

    st.markdown("#### Logs")
    if logs_df.empty:
        st.info("No logs available yet.")
    else:
        levels = sorted(logs_df["level"].dropna().unique().tolist())
        selected_levels = st.multiselect("Filter Levels", levels, default=levels)
        filtered_logs = logs_df[logs_df["level"].isin(selected_levels)]
        st.dataframe(filtered_logs.sort_values("timestamp", ascending=False), width="stretch", height=280)

    st.markdown("#### Traces")
    if traces_df.empty:
        st.info("No traces available yet.")
    else:
        event_counts = (
            traces_df["event"]
            .value_counts()
            .rename_axis("event")
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        c_left, c_right = st.columns(2)
        with c_left:
            st.caption("Event Counts")
            st.bar_chart(event_counts.set_index("event"))
        with c_right:
            turn_end = traces_df[traces_df["event"].isin(["turn.end", "ui.turn.end"])].copy()
            if not turn_end.empty:
                turn_end["elapsed_ms"] = turn_end["payload"].apply(
                    lambda p: p.get("elapsed_ms") if isinstance(p, dict) else None
                )
                latency_series = turn_end.dropna(subset=["elapsed_ms"]).set_index("timestamp_utc")["elapsed_ms"]
                if not latency_series.empty:
                    st.caption("Latency Over Time (ms)")
                    st.line_chart(latency_series)
                else:
                    st.caption("Latency Over Time (ms)")
                    st.info("No latency data in traces yet.")
            else:
                st.caption("Latency Over Time (ms)")
                st.info("No turn end events yet.")

        preview = traces_df.copy()
        preview["payload"] = preview["payload"].apply(
            lambda p: json.dumps(p, ensure_ascii=False) if isinstance(p, dict) else str(p)
        )
        st.dataframe(preview.sort_values("timestamp_utc", ascending=False), width="stretch", height=280)

        st.markdown("#### Trace Explorer")
        turns = (
            traces_df["turn_id"]
            .dropna()
            .astype(str)
            .loc[lambda s: s != "unknown"]
            .drop_duplicates()
            .tolist()
        )
        if turns:
            selected_turn = st.selectbox("Chon turn_id", options=list(reversed(turns)))
            turn_df = traces_df[traces_df["turn_id"] == selected_turn].copy()
            turn_df = turn_df.sort_values("timestamp_utc", ascending=True).reset_index(drop=True)
            if not turn_df.empty:
                compact = turn_df[["timestamp_utc", "event"]].copy()
                st.dataframe(compact, width="stretch", height=220)

                for idx, row in turn_df.iterrows():
                    title = f"Step {idx + 1}: {row['event']} @ {row['timestamp_utc']}"
                    with st.expander(title, expanded=False):
                        payload = row.get("payload", {})
                        if isinstance(payload, dict):
                            st.json(payload, expanded=True)
                        else:
                            st.write(payload)
            else:
                st.info("Khong co step nao cho turn nay.")
        else:
            st.info("Chua co turn_id hop le de inspect.")


def main() -> None:
    st.set_page_config(page_title="TravelBuddy Studio", page_icon="🌏", layout="wide")
    render_travel_header()
    view = st.segmented_control("Workspace", options=["Travel Chat", "Observability"], default="Travel Chat")
    if view == "Travel Chat":
        chat_tab()
    else:
        observability_tab()


if __name__ == "__main__":
    main()
