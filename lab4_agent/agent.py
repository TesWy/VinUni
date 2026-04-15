import os
import time
import uuid
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict

from observability import LOG_FILE, TRACE_FILE, get_logger, set_current_turn_id, write_trace
from response_utils import render_message_content
from tools import calculate_budget, convert_currency, get_weather, search_flights, search_hotels

load_dotenv()
LOGGER = get_logger("travelbuddy.agent")

# 1. Doc system prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


# 2. Khai bao state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 3. Khoi tao LLM va tools
tools_list = [search_flights, search_hotels, calculate_budget, get_weather, convert_currency]
provider = os.getenv("LLM_PROVIDER", "gemini").lower()
if provider == "openai":
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
else:
    llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemma-4-31b-it"))
llm_with_tools = llm.bind_tools(tools_list)


# 4. Agent node
def agent_node(state: AgentState, config: RunnableConfig):
    turn_id = config.get("configurable", {}).get("turn_id", "unknown")
    set_current_turn_id(turn_id)
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    LOGGER.info("agent_node start | turn_id=%s | message_count=%s", turn_id, len(messages))
    write_trace(
        "agent.node.start",
        {"message_count": len(messages)},
        turn_id=turn_id,
    )
    response = llm_with_tools.invoke(messages)

    # === LOGGING ===
    if response.tool_calls:
        LOGGER.info("agent_node produced tool calls | turn_id=%s | count=%s", turn_id, len(response.tool_calls))
        for tc in response.tool_calls:
            write_trace(
                "agent.tool_call",
                {"tool_name": tc["name"], "args": tc["args"]},
                turn_id=turn_id,
            )
            print(f"[Goi tool: {tc['name']}({tc['args']})]")
    else:
        LOGGER.info("agent_node produced direct response | turn_id=%s", turn_id)
        print("[Tra loi truc tiep]")

    write_trace(
        "agent.response",
        {
            "has_tool_calls": bool(response.tool_calls),
            "tool_call_count": len(response.tool_calls) if response.tool_calls else 0,
            "content_preview": render_message_content(response.content)[:300],
            "raw_content": response.content,
        },
        turn_id=turn_id,
    )
    return {"messages": [response]}


# 5. Xay dung graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()


# 6. Chat loop
if __name__ == "__main__":
    print(f"Log file: {LOG_FILE}")
    print(f"Trace file: {TRACE_FILE}")
    print("=" * 60)
    print("TravelBuddy - Tro ly Du lich Thong minh")
    print("Go 'quit' de thoat")
    print("=" * 60)

    while True:
        user_input = input("\nBan: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        turn_id = str(uuid.uuid4())
        set_current_turn_id(turn_id)
        turn_start = time.perf_counter()
        LOGGER.info("turn start | turn_id=%s | user_input=%s", turn_id, user_input)
        write_trace("turn.start", {"user_input": user_input}, turn_id=turn_id)

        print("\nTravelBuddy dang suy nghi...")
        try:
            result = graph.invoke({"messages": [("human", user_input)]}, config={"configurable": {"turn_id": turn_id}})
        except Exception as exc:
            LOGGER.exception("turn failed | turn_id=%s", turn_id)
            write_trace("turn.error", {"error": str(exc)}, turn_id=turn_id)
            print(f"\nTravelBuddy: Loi he thong: {exc}")
            continue
        final = result["messages"][-1]
        elapsed_ms = int((time.perf_counter() - turn_start) * 1000)
        LOGGER.info("turn end | turn_id=%s | elapsed_ms=%s", turn_id, elapsed_ms)
        write_trace(
            "turn.end",
            {"elapsed_ms": elapsed_ms, "final_preview": render_message_content(getattr(final, "content", ""))[:500]},
            turn_id=turn_id,
        )
        print(f"\nTravelBuddy: {render_message_content(final.content)}")
