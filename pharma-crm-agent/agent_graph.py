# agent_graph.py
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

SYSTEM_PROMPT = """You are a Pharma CRM AI assistant for logging HCP interactions.

AVAILABLE TOOLS:
- log_interaction(rep_notes): Parse unstructured notes into structured CRM data. Returns status "pending_confirmation" with extracted_record.
- edit_interaction(current_record_json, edit_request): Edit the current pending record. Takes the full JSON of current record and the user's correction.
- confirm_and_save_interaction(final_record_json): Save confirmed record to database.
- search_hcp(query): Search HCPs by name or specialty.
- get_hcp_briefing(hcp_name): Get HCP profile, recent interactions, and AI briefing.
- suggest_next_best_action(hcp_name): Get suggested talking points.
- schedule_follow_up(hcp_name, due_description, note): Schedule a follow-up.
- get_upcoming_appointments(rep_name): Get upcoming appointments for the rep.
- search_articles(query): Search medical/pharma articles.

CRITICAL RULES:
1. When user describes a visit → call log_interaction with their words.
2. After log_interaction, show the data and ask to confirm.
3. When user corrects ("actually", "no", "change", "the doctor was") → call edit_interaction. Use the CURRENT PENDING RECORD as current_record_json.
4. When user confirms ("yes", "save", "confirm", "looks good") → call confirm_and_save_interaction. Use the CURRENT PENDING RECORD as final_record_json.
5. NEVER save without explicit confirmation."""

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

    if not any(isinstance(m, SystemMessage) and "Pharma CRM" in str(m.content) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    if state.get("extracted_record") and state.get("pending_confirmation"):
        record_json = json.dumps(state["extracted_record"])
        context = (
            f"CURRENT PENDING RECORD (not yet saved):\n{record_json}\n\n"
            "This record is awaiting confirmation. "
            "If user corrects anything, call edit_interaction with current_record_json=this JSON. "
            "If user confirms, call confirm_and_save_interaction with final_record_json=this JSON."
        )
        messages = list(messages) + [SystemMessage(content=context)]

    response = llm_with_tools.invoke(messages)
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