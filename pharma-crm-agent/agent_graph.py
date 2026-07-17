# agent_graph.py
import re
import json
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from agent_tools import (
    llm, log_interaction, edit_interaction, confirm_and_save_interaction,
    search_hcp, get_hcp_briefing, suggest_next_best_action, schedule_follow_up,
    get_upcoming_appointments, search_articles)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    extracted_record: Optional[dict]
    pending_confirmation: bool

SYSTEM_PROMPT = """You are a Pharma CRM AI assistant. You help pharmaceutical sales reps log HCP interactions.

== RESPONSE FORMAT ==
- Write responses in plain, friendly language. Use **bold** for field labels.
- Show extracted data as a bulleted list with **Field Name**: value format.
- Add blank lines between paragraphs. Keep responses concise.
- NEVER output tool names, function names, or code in your response text.

== TOOLS ==
- log_interaction: Parse notes into structured CRM data. Takes rep_notes (string).
- edit_interaction: Edit pending record. Takes current_record_json (object) and edit_request (string).
- confirm_and_save_interaction: Save record to DB. Takes final_record_json (object - the full record as a JSON object).
- search_hcp: Search doctors by name/specialty. Takes query (string).
- get_hcp_briefing: Get doctor profile and history. Takes hcp_name (string).
- suggest_next_best_action: Get visit suggestions. Takes hcp_name (string).
- schedule_follow_up: Create follow-up task. Takes hcp_name, due_description, note.
- get_upcoming_appointments: Get upcoming visits. Takes rep_name (string).
- search_articles: Search medical articles. Takes query (string).

== RULES ==
1. When user describes a visit/call → call ONLY log_interaction. Pass their ENTIRE message as rep_notes. Do NOT call any other tool.
2. After log_interaction extracts data → show the extracted fields clearly as a bulleted list and ask: "Does this look correct?"
3. When user says "yes", "confirm", "save", "looks good" → call ONLY confirm_and_save_interaction. Pass the EXACT pending record object as final_record_json. Do NOT reconstruct or modify it.
4. When user corrects ("actually", "no", "change", "wrong") → call ONLY edit_interaction.
5. NEVER save without explicit user confirmation.
6. Call ONLY ONE tool per response. Never call multiple tools at once.
7. NEVER write tool names (log_interaction, confirm_and_save_interaction, search_hcp, etc.) in your response text. The tools are called silently.
8. If a search finds no results, say so in plain language and offer to log the interaction anyway.
9. For greetings or general questions, respond directly without calling tools."""

TOOL_NAMES = [
    "log_interaction", "edit_interaction", "confirm_and_save_interaction",
    "search_hcp", "get_hcp_briefing", "suggest_next_best_action",
    "schedule_follow_up", "get_upcoming_appointments", "search_articles"
]

def _strip_tool_names(text: str) -> str:
    """Remove leaked tool names from AI response text."""
    if not text:
        return text
    cleaned = text
    for name in TOOL_NAMES:
        cleaned = re.sub(rf'\b{re.escape(name)}[\s]*[\(:]?', '', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

tools = [log_interaction, edit_interaction, confirm_and_save_interaction,
          search_hcp, get_hcp_briefing, suggest_next_best_action, schedule_follow_up,
          get_upcoming_appointments, search_articles]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)

# =====================================================================
# NODE: Chatbot (decides which tool to call)
# =====================================================================

def chatbot(state: AgentState):
    messages = state["messages"]

    if not any(isinstance(m, SystemMessage) and "Pharma CRM AI assistant" in str(m.content) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    if state.get("extracted_record") and state.get("pending_confirmation"):
        record_json = json.dumps(state["extracted_record"], indent=2)
        context = (
            "=== PENDING RECORD (awaiting user confirmation) ===\n"
            f"{record_json}\n"
            "=== END PENDING RECORD ===\n\n"
            "The above record was extracted from the rep's notes. Show these fields to the user as a bulleted list "
            "using **Field Name**: value format and ask them to confirm.\n\n"
            "IMPORTANT: When the user confirms (says 'yes', 'confirm', 'save', 'looks good'), "
            "you MUST call confirm_and_save_interaction with the final_record_json parameter set to "
            "the EXACT record object shown above (as a JSON object, not a string). Pass the record directly."
            "Do NOT add, remove, or rename any fields.\n\n"
            "If the user wants to make corrections, call edit_interaction instead."
        )
        messages = list(messages) + [SystemMessage(content=context)]

    response = llm_with_tools.invoke(messages)

    if hasattr(response, "content") and response.content:
        cleaned = _strip_tool_names(str(response.content))
        if cleaned:
            response.content = cleaned
        elif not response.tool_calls:
            response.content = "I've processed your request. Is there anything else you need?"

    return {"messages": [response]}

# =====================================================================
# NODE: Update state from tool output
# =====================================================================

def update_state_from_tools(state: AgentState):
    """Read tool results and update extracted_record and pending_confirmation in state."""
    messages = state["messages"]
    extracted = state.get("extracted_record")
    pending = state.get("pending_confirmation", False)

    for msg in reversed(messages):
        content = msg.content if hasattr(msg, 'content') else None
        if not content or not isinstance(content, str):
            continue
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                continue
            status = data.get("status", "")
            if status == "pending_confirmation" and data.get("extracted_record"):
                extracted = data["extracted_record"]
                pending = True
                break
            elif status == "updated" and data.get("updated_record"):
                extracted = data["updated_record"]
                pending = True
                break
            elif status == "committed_to_db":
                extracted = None
                pending = False
                break
        except:
            pass

    return {"extracted_record": extracted, "pending_confirmation": pending}

# =====================================================================
# ROUTER: Where to go next
# =====================================================================

def route_next(state: AgentState):
    """Route to tools or end based on LLM response."""
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# =====================================================================
# BUILD GRAPH
# =====================================================================

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("chatbot", chatbot)
    workflow.add_node("tools", tool_node)
    workflow.add_node("update_state", update_state_from_tools)

    workflow.set_entry_point("chatbot")
    workflow.add_conditional_edges("chatbot", route_next, {"tools": "tools", END: END})
    workflow.add_edge("tools", "update_state")
    workflow.add_edge("update_state", "chatbot")

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

app = build_graph()
