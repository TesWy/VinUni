import contextlib
import io
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable


BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

from agent import graph, provider  # noqa: E402
from observability import get_logger, write_trace  # noqa: E402
from response_utils import normalize_response_text, render_message_content  # noqa: E402


LOGGER = get_logger("travelbuddy.eval")
EVAL_DIR = BASE_DIR / "logs" / "evals"
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def _strip_accents(text: str) -> str:
    import unicodedata

    text = text.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _norm(text: str) -> str:
    return " ".join(_strip_accents(str(text or "")).lower().split())


def _contains_any(text: str, keywords: list[str]) -> bool:
    haystack = _norm(text)
    return any(_norm(keyword) in haystack for keyword in keywords)


def _count_categories(text: str, categories: list[list[str]]) -> int:
    haystack = _norm(text)
    count = 0
    for category in categories:
        if any(_norm(keyword) in haystack for keyword in category):
            count += 1
    return count


@dataclass
class EvalCase:
    case_id: str
    title: str
    user_input: str
    expectation: str
    evaluator: Callable[[dict], list[dict]]


@dataclass
class ToolCallRecord:
    name: str
    args: dict = field(default_factory=dict)


@dataclass
class ToolResultRecord:
    name: str
    content: str


@dataclass
class EvalResult:
    case_id: str
    title: str
    user_input: str
    expectation: str
    turn_id: str
    elapsed_ms: int
    passed: bool
    checks: list[dict]
    tool_calls: list[dict]
    tool_results: list[dict]
    final_answer: str


def evaluate_direct_answer(run: dict) -> list[dict]:
    final_answer = run["final_answer"]
    checks = []
    checks.append(
        {
            "name": "No tool call",
            "passed": len(run["tool_calls"]) == 0,
            "details": f"tool_calls={len(run['tool_calls'])}",
        }
    )
    asked_categories = _count_categories(
        final_answer,
        [
            ["so thich", "thich bien", "thich nui", "thich thanh pho", "muon di dau", "khong gian nao", "dung gu"],
            ["ngan sach", "budget", "chi phi", "khoang bao nhieu"],
            ["thoi gian", "ngay di", "di may ngay", "khi nao", "bao lau", "thoi diem nao", "trong bao lau"],
        ],
    )
    checks.append(
        {
            "name": "Asks follow-up questions",
            "passed": ("?" in final_answer) and asked_categories >= 2,
            "details": f"question_marks={final_answer.count('?')}, matched_categories={asked_categories}",
        }
    )
    return checks


def evaluate_single_tool_search_flights(run: dict) -> list[dict]:
    tool_names = [call["name"] for call in run["tool_calls"]]
    checks = [
        {
            "name": "Uses search_flights only",
            "passed": tool_names == ["search_flights"],
            "details": f"tool_sequence={tool_names}",
        }
    ]

    matching_result = next((result for result in run["tool_results"] if result["name"] == "search_flights"), None)
    if matching_result:
        flight_lines = [
            line for line in matching_result["content"].splitlines() if line.strip() and line.strip()[0].isdigit() and "." in line
        ]
        checks.append(
            {
                "name": "search_flights returns 4 options",
                "passed": len(flight_lines) == 4,
                "details": f"flight_option_count={len(flight_lines)}",
            }
        )
    else:
        checks.append(
            {
                "name": "search_flights returns 4 options",
                "passed": False,
                "details": "tool output for search_flights not captured",
            }
        )

    checks.append(
        {
            "name": "Final answer mentions route or flight options",
            "passed": _contains_any(
                run["final_answer"],
                ["ha noi", "da nang", "vietjet", "vietnam airlines", "bamboo"],
            ),
            "details": "expected route/airline mention in final answer",
        }
    )
    return checks


def evaluate_multi_step_trip(run: dict) -> list[dict]:
    tool_names = [call["name"] for call in run["tool_calls"]]
    expected_sequence = ["search_flights", "search_hotels", "calculate_budget"]
    checks = [
        {
            "name": "Uses expected multi-step tool chain",
            "passed": tool_names == expected_sequence,
            "details": f"expected={expected_sequence}, actual={tool_names}",
        },
        {
            "name": "Mentions budget synthesis in final answer",
            "passed": _contains_any(
                run["final_answer"],
                ["tong chi", "con lai", "ngan sach", "5 trieu"],
            ),
            "details": "expected budget summary in final answer",
        },
    ]
    return checks


def evaluate_missing_info_clarification(run: dict) -> list[dict]:
    final_answer = run["final_answer"]
    matched_categories = _count_categories(
        final_answer,
        [
            ["thanh pho", "o dau", "diem den"],
            ["bao nhieu dem", "may dem", "thoi gian"],
            ["ngan sach", "budget", "gia toi da"],
        ],
    )
    return [
        {
            "name": "No tool call before clarification",
            "passed": len(run["tool_calls"]) == 0,
            "details": f"tool_calls={len(run['tool_calls'])}",
        },
        {
            "name": "Asks for city, nights, and budget",
            "passed": ("?" in final_answer) and matched_categories >= 2,
            "details": f"question_marks={final_answer.count('?')}, matched_categories={matched_categories}",
        },
    ]


def evaluate_guardrail_refusal(run: dict) -> list[dict]:
    final_answer = run["final_answer"]
    return [
        {
            "name": "No tool call on off-topic request",
            "passed": len(run["tool_calls"]) == 0,
            "details": f"tool_calls={len(run['tool_calls'])}",
        },
        {
            "name": "Politely refuses and redirects to travel scope",
            "passed": _contains_any(
                final_answer,
                ["khong ho tro", "chi ho tro", "du lich", "ve may bay", "khach san"],
            ),
            "details": "expected refusal scoped to travel assistant",
        },
    ]


CASES = [
    EvalCase(
        case_id="test_1",
        title="Direct Answer (Khong can tool)",
        user_input="Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.",
        expectation="Agent chao hoi, hoi them ve so thich / ngan sach / thoi gian. Khong goi tool nao.",
        evaluator=evaluate_direct_answer,
    ),
    EvalCase(
        case_id="test_2",
        title="Single Tool Call",
        user_input="Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng",
        expectation='Goi search_flights("Hà Nội", "Đà Nẵng"), liet ke 4 chuyen bay.',
        evaluator=evaluate_single_tool_search_flights,
    ),
    EvalCase(
        case_id="test_3",
        title="Multi-Step Tool Chaining",
        user_input="Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!",
        expectation=(
            'Ky vong chain: search_flights("Hà Nội", "Phú Quốc") -> '
            'search_hotels("Phú Quốc", max_price phu hop) -> '
            'calculate_budget(5000000, ...), roi tong hop thanh goi y hoan chinh.'
        ),
        evaluator=evaluate_multi_step_trip,
    ),
    EvalCase(
        case_id="test_4",
        title="Missing Info / Clarification",
        user_input="Tôi muốn đặt khách sạn",
        expectation="Agent hoi lai thanh pho nao, bao nhieu dem, ngan sach bao nhieu. Khong goi tool voi.",
        evaluator=evaluate_missing_info_clarification,
    ),
    EvalCase(
        case_id="test_5",
        title="Guardrail / Refusal",
        user_input="Giải giúp tôi bài tập lập trình Python về linked list",
        expectation="Tu choi lich su, noi rang chi ho tro ve du lich.",
        evaluator=evaluate_guardrail_refusal,
    ),
]


def _extract_messages(node_payload: dict) -> list:
    if not isinstance(node_payload, dict):
        return []
    messages = node_payload.get("messages")
    if isinstance(messages, list):
        return messages
    return []


def run_case(case: EvalCase) -> EvalResult:
    turn_id = f"eval-{case.case_id}-{uuid.uuid4().hex[:8]}"
    tool_calls: list[ToolCallRecord] = []
    tool_results: list[ToolResultRecord] = []
    final_answer = ""
    started = time.perf_counter()

    LOGGER.info("eval case start | case_id=%s | turn_id=%s", case.case_id, turn_id)
    write_trace(
        "eval.case.start",
        {"case_id": case.case_id, "title": case.title, "user_input": case.user_input},
        turn_id=turn_id,
    )

    with contextlib.redirect_stdout(io.StringIO()):
        for update in graph.stream(
            {"messages": [("human", case.user_input)]},
            config={"configurable": {"turn_id": turn_id, "pane": "eval"}},
            stream_mode="updates",
        ):
            if not isinstance(update, dict):
                continue

            for node_name, node_payload in update.items():
                messages = _extract_messages(node_payload)
                for message in messages:
                    current_tool_calls = getattr(message, "tool_calls", None)
                    if current_tool_calls:
                        for call in current_tool_calls:
                            tool_calls.append(ToolCallRecord(name=call["name"], args=call.get("args", {})))

                    message_type = getattr(message, "type", "")
                    if message_type == "tool":
                        tool_results.append(
                            ToolResultRecord(
                                name=getattr(message, "name", node_name),
                                content=normalize_response_text(getattr(message, "content", "")),
                            )
                        )

                    if message_type in ("ai", "AIMessage") and not current_tool_calls:
                        final_answer = render_message_content(getattr(message, "content", ""))

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    run_payload = {
        "tool_calls": [asdict(item) for item in tool_calls],
        "tool_results": [asdict(item) for item in tool_results],
        "final_answer": final_answer,
    }
    checks = case.evaluator(run_payload)
    passed = all(check["passed"] for check in checks)

    write_trace(
        "eval.case.end",
        {
            "case_id": case.case_id,
            "title": case.title,
            "elapsed_ms": elapsed_ms,
            "passed": passed,
            "tool_sequence": [item.name for item in tool_calls],
        },
        turn_id=turn_id,
    )
    LOGGER.info(
        "eval case end | case_id=%s | turn_id=%s | passed=%s | elapsed_ms=%s",
        case.case_id,
        turn_id,
        passed,
        elapsed_ms,
    )

    return EvalResult(
        case_id=case.case_id,
        title=case.title,
        user_input=case.user_input,
        expectation=case.expectation,
        turn_id=turn_id,
        elapsed_ms=elapsed_ms,
        passed=passed,
        checks=checks,
        tool_calls=[asdict(item) for item in tool_calls],
        tool_results=[asdict(item) for item in tool_results],
        final_answer=final_answer,
    )


def format_markdown_report(results: list[EvalResult], model_name: str) -> str:
    passed_count = sum(1 for result in results if result.passed)
    lines = [
        "# TravelBuddy Eval Report",
        "",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Provider: `{provider}`",
        f"- Model: `{model_name}`",
        f"- Passed: **{passed_count}/{len(results)}**",
        "",
        "## Summary",
        "",
        "| Case | Status | Tools Used | Latency |",
        "| --- | --- | --- | --- |",
    ]

    for result in results:
        tools = ", ".join(call["name"] for call in result.tool_calls) if result.tool_calls else "None"
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"| {result.case_id} | {status} | {tools} | {result.elapsed_ms} ms |")

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.case_id}: {result.title}",
                "",
                f"- Status: **{'PASS' if result.passed else 'FAIL'}**",
                f"- Turn ID: `{result.turn_id}`",
                f"- Latency: `{result.elapsed_ms} ms`",
                "",
                "**User Input**",
                "",
                "```text",
                result.user_input,
                "```",
                "",
                "**Expectation**",
                "",
                "```text",
                result.expectation,
                "```",
                "",
                "**Checks**",
                "",
            ]
        )
        for check in result.checks:
            lines.append(f"- [{'PASS' if check['passed'] else 'FAIL'}] {check['name']} | {check['details']}")

        lines.extend(["", "**Tools Used**", ""])
        if result.tool_calls:
            for idx, call in enumerate(result.tool_calls, start=1):
                lines.append(f"{idx}. `{call['name']}` with args `{json.dumps(call['args'], ensure_ascii=False)}`")
        else:
            lines.append("- None")

        lines.extend(["", "**Tool Outputs**", ""])
        if result.tool_results:
            for idx, tool_result in enumerate(result.tool_results, start=1):
                lines.extend(
                    [
                        f"{idx}. `{tool_result['name']}`",
                        "```text",
                        tool_result["content"],
                        "```",
                    ]
                )
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "**Final Answer**",
                "",
                "```text",
                result.final_answer or "<empty>",
                "```",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    model_name = (
        os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if provider == "openai"
        else os.getenv("GEMINI_MODEL", "gemma-4-31b-it")
    )

    results = [run_case(case) for case in CASES]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = EVAL_DIR / f"eval_{timestamp}.json"
    md_path = EVAL_DIR / f"eval_{timestamp}.md"
    latest_json = EVAL_DIR / "eval_latest.json"
    latest_md = EVAL_DIR / "eval_latest.md"

    json_payload = {
        "timestamp": datetime.now().isoformat(),
        "provider": provider,
        "model": model_name,
        "summary": {
            "passed": sum(1 for result in results if result.passed),
            "total": len(results),
        },
        "results": [asdict(result) for result in results],
    }
    markdown = format_markdown_report(results, model_name)

    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")

    print(f"Saved JSON report: {json_path}")
    print(f"Saved Markdown report: {md_path}")
    print(f"Latest Markdown report: {latest_md}")
    print()
    for result in results:
        tool_names = [call["name"] for call in result.tool_calls]
        print(f"{result.case_id}: {'PASS' if result.passed else 'FAIL'} | tools={tool_names} | {result.elapsed_ms} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
