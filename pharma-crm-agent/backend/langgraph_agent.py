# backend/langgraph_agent.py
import os
import json
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from database import SessionLocal
from models import Interaction

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path, override=True)

# Initialize Groq - using llama-3.1-8b-instant (fast, low rate-limit)
llm = ChatGroq(
    temperature=0.0,
    model_name="llama-3.1-8b-instant",
    groq_api_key=os.getenv("GROQ_API_KEY"),
)


# =====================================================================
# HELPER: Fetch latest interaction for a thread
# =====================================================================

def get_latest_interaction(thread_id: str) -> Optional[dict]:
    """Fetch the most recent interaction record for a given thread_id."""
    try:
        db = SessionLocal()
        interaction = (
            db.query(Interaction)
            .filter(Interaction.thread_id == thread_id)
            .order_by(Interaction.updated_at.desc())
            .first()
        )
        db.close()
        if interaction:
            record = {
                "id": interaction.id,
                "hcpName": interaction.hcp_name,
                "interactionType": interaction.interaction_type,
                "duration": interaction.duration,
                "sentiment": interaction.sentiment,
                "topicsDiscussed": interaction.topics_discussed,
                "outcomes": interaction.outcomes or "",
                "followUpActions": interaction.follow_up_actions or "",
                "attendees": interaction.attendees or "",
            }
            print(f"[DB] Loaded record id={interaction.id} for thread={thread_id}: {record}")
            return record
    except Exception as e:
        print(f"[DB ERROR] get_latest_interaction: {e}")
    return None


def save_interaction(record: dict, thread_id: str, interaction_id: int = None) -> int:
    """
    Save or update an interaction in the database.
    If interaction_id is provided, UPDATE the existing record.
    Otherwise INSERT a new record.
    Returns the interaction id.
    """
    try:
        db = SessionLocal()
        if interaction_id:
            interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if interaction:
                interaction.hcp_name = record.get("hcpName", interaction.hcp_name)
                interaction.interaction_type = record.get("interactionType", interaction.interaction_type)
                interaction.duration = record.get("duration", interaction.duration)
                interaction.sentiment = record.get("sentiment", interaction.sentiment)
                interaction.topics_discussed = record.get("topicsDiscussed", interaction.topics_discussed)
                interaction.outcomes = record.get("outcomes", interaction.outcomes)
                interaction.follow_up_actions = record.get("followUpActions", interaction.follow_up_actions)
                interaction.attendees = record.get("attendees", interaction.attendees)
                db.commit()
                rid = interaction.id
                db.close()
                print(f"[DB] Updated record id={rid}")
                return rid

        interaction = Interaction(
            hcp_name=record.get("hcpName", ""),
            interaction_type=record.get("interactionType", ""),
            duration=record.get("duration", 0),
            sentiment=record.get("sentiment", "neutral"),
            topics_discussed=record.get("topicsDiscussed", ""),
            outcomes=record.get("outcomes", ""),
            follow_up_actions=record.get("followUpActions", ""),
            attendees=record.get("attendees", ""),
            thread_id=thread_id,
        )
        db.add(interaction)
        db.commit()
        rid = interaction.id
        db.close()
        print(f"[DB] Inserted new record id={rid}")
        return rid
    except Exception as e:
        print(f"[DB ERROR] save_interaction: {e}")
        return None


# =====================================================================
# TOOLS
# =====================================================================

@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    duration: str,
    sentiment: str,
    topics_discussed: str,
    outcomes: str = "",
    follow_up_actions: str = "",
    attendees: str = "",
) -> dict:
    """
    Logs a NEW CRM interaction record.
    Always use this for first-time full descriptions.
    duration should be a numeric string like "30".
    """
    try:
        dur = int(duration)
    except (ValueError, TypeError):
        dur = 30  # default

    record = {
        "hcpName": hcp_name,
        "interactionType": interaction_type,
        "duration": dur,
        "sentiment": sentiment,
        "topicsDiscussed": topics_discussed,
        "outcomes": outcomes,
        "followUpActions": follow_up_actions,
        "attendees": attendees,
    }
    return {"action": "log", "record": record, "saved": True}


@tool
def update_record(
    field: str,
    value: str,
) -> dict:
    """
    Updates a single field in the current interaction record.
    Use this for partial corrections like 'doctor name is X' or 'duration is 20'.
    Valid fields: hcpName, interactionType, duration, sentiment, topicsDiscussed, outcomes, followUpActions, attendees.
    value should always be a string, even for duration.
    """
    return {"action": "update", "field": field, "value": value, "saved": True}


@tool
def save_record() -> dict:
    """
    Persists the current record to the database.
    Call this AFTER log_interaction or after making corrections with update_record.
    """
    return {"action": "save", "saved": True}


@tool
def get_upcoming_appointments(hcp_name: str) -> str:
    """Returns upcoming appointments for a given HCP."""
    return f"No upcoming appointments found for {hcp_name}. Consider scheduling a follow-up visit."


@tool
def get_hcp_details(hcp_name: str) -> str:
    """Returns details about a Healthcare Professional."""
    try:
        db = SessionLocal()
        interactions = db.query(Interaction).filter(
            Interaction.hcp_name.ilike(f"%{hcp_name}%")
        ).all()
        db.close()

        if not interactions:
            return f"No records found for {hcp_name}."

        details = []
        for i in interactions:
            details.append(f"- {i.interaction_type} on {i.created_at}: {i.topics_discussed} (Sentiment: {i.sentiment})")

        return f"History for {hcp_name}:\n" + "\n".join(details)
    except Exception as e:
        return f"Error fetching details: {str(e)}"


@tool
def search_articles(query: str) -> str:
    """Searches for medical/pharmaceutical articles related to a topic."""
    return f"Found 3 articles related to '{query}':\n1. Efficacy Study 2024\n2. Clinical Trial Results\n3. Patient Outcomes Review"


# =====================================================================
# STATE
# =====================================================================

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_record: Optional[dict]
    interaction_id: Optional[int]


# =====================================================================
# TOOLS LIST & GRAPH
# =====================================================================

tools = [log_interaction, update_record, save_record, get_upcoming_appointments, get_hcp_details, search_articles]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)

SYSTEM_PROMPT = """You are a CRM AI assistant for pharmaceutical sales reps.

You have a 'current_record' (previously extracted data) and a 'user_message'.

BEHAVIOR:
- If the user provides a FULL meeting summary (e.g. "I met with Dr. X for 30 minutes about Product Y"), extract ALL fields using log_interaction.
- If the user provides a simple value (e.g. "aakib shaikh", "45", "neutral"), assume they want to UPDATE the specific corresponding field in the previous JSON record WITHOUT requiring trigger words like "change" or "actually". Infer the intent from context.
- If current_record is NULL, treat the message as a fresh record.
- If the message is vague and missing data, infer reasonable defaults (duration: 30, sentiment: neutral, interactionType: visit).

AVAILABLE TOOLS:
- log_interaction(hcp_name, interaction_type, duration, sentiment, topics_discussed, outcomes, follow_up_actions, attendees)
- update_record(field, value) -- field must be one of: hcpName, interactionType, duration, sentiment, topicsDiscussed, outcomes, followUpActions, attendees
- save_record()

RULES:
1. ALWAYS call save_record() after log_interaction or update_record.
2. Names must be properly capitalized (e.g. "Dr. Aadil Khan" not "dr. aadil khan").
3. Be concise and professional in your responses.
4. For queries (not updates), answer directly without calling tools.
5. NEVER return an error rejection message — if you cannot determine the field, guess the most likely one based on the value type.

IMPORTANT: After calling tools, respond with a brief confirmation of what you did."""


def chatbot(state: AgentState):
    """Process user message and decide next action."""
    try:
        messages = list(state["messages"])
        current_record = state.get("current_record")
        interaction_id = state.get("interaction_id")

        # Build the system message with current record context
        system_content = SYSTEM_PROMPT
        if current_record:
            system_content += f"\n\nCURRENT RECORD (id={interaction_id}):\n{json.dumps(current_record, indent=2)}"
        else:
            system_content += "\n\nCURRENT RECORD: None (fresh interaction)"

        messages = [SystemMessage(content=system_content)] + messages

        print(f"[LLM] Calling model with {len(messages)} messages...")
        response = llm_with_tools.invoke(messages)
        print(f"[LLM] Response tool_calls: {[tc['name'] for tc in response.tool_calls] if response.tool_calls else 'none'}")
        return {"messages": [response]}
    except Exception as e:
        print(f"[LLM ERROR] chatbot failed: {e}")
        return {"messages": [AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")]}


def _coerce_int(val) -> int:
    """Safely convert a value to int."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def process_tools(state: AgentState):
    """Process tool calls and maintain current_record state with full error catching."""
    current_record = dict(state.get("current_record") or {})
    interaction_id = state.get("interaction_id")

    try:
        # Find the last AIMessage that has tool_calls (not the ToolMessage)
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    name = tool_call["name"]
                    args = tool_call["args"]

                    print(f"[TOOLS] Executing: {name}({args})")

                    if name == "log_interaction":
                        current_record = {
                            "hcpName": args.get("hcp_name", ""),
                            "interactionType": args.get("interaction_type", ""),
                            "duration": _coerce_int(args.get("duration", 30)),
                            "sentiment": args.get("sentiment", "neutral"),
                            "topicsDiscussed": args.get("topics_discussed", ""),
                            "outcomes": args.get("outcomes", ""),
                            "followUpActions": args.get("follow_up_actions", ""),
                            "attendees": args.get("attendees", ""),
                        }
                        print(f"[STATE] Full record set: {current_record}")

                    elif name == "update_record":
                        field = args.get("field", "")
                        value = args.get("value", "")
                        if field == "duration":
                            value = _coerce_int(value)
                        current_record[field] = value
                        print(f"[STATE] Updated field '{field}' = {value}")
                        print(f"[STATE] Current record: {current_record}")

                    elif name == "save_record":
                        print(f"[STATE] Save requested. Record: {current_record}")
                break
    except Exception as e:
        print(f"[STATE ERROR] process_tools failed: {e}")

    return {"current_record": current_record, "interaction_id": interaction_id}


def route_next(state: AgentState):
    """Route to tools or end based on LLM response."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_agent():
    """Build and compile the LangGraph agent."""
    workflow = StateGraph(AgentState)
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("tools", tool_node)
    workflow.add_node("update_state", process_tools)
    workflow.set_entry_point("chatbot")
    workflow.add_conditional_edges("chatbot", route_next, {"tools": "tools", END: END})
    workflow.add_edge("tools", "update_state")
    workflow.add_edge("update_state", "chatbot")
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


agent_app = build_agent()


# =====================================================================
# SUGGESTIONS GENERATOR
# =====================================================================

def _generate_suggestions(record: dict) -> list:
    """Generate contextual follow-up suggestions based on the record."""
    suggestions = []
    if record.get("hcpName"):
        suggestions.append(f"Schedule a follow-up with {record['hcpName']}")
    if record.get("topicsDiscussed"):
        suggestions.append("Send relevant brochures via email")
    suggestions.append("Log another interaction")
    return suggestions[:3]


# =====================================================================
# MAIN AGENT FUNCTION
# =====================================================================

def run_agent(message: str, thread_id: str = "default") -> dict:
    """
    Run the agent with a user message and return the response in the format
    expected by the frontend.

    Returns:
        {
            "aiReply": str,
            "extractedData": dict | None,
            "aiSuggestions": list[str]
        }
    """
    print(f"\n{'='*60}")
    print(f"[INCOMING] message: '{message}' | thread_id: '{thread_id}'")
    print(f"{'='*60}")

    config = {"configurable": {"thread_id": thread_id}}

    # Fetch previous record for this thread
    try:
        previous = get_latest_interaction(thread_id)
    except Exception as e:
        print(f"[DB ERROR] get_latest_interaction failed: {e}")
        previous = None
    interaction_id = previous["id"] if previous else None

    try:
        result = agent_app.invoke(
            {
                "messages": [HumanMessage(content=message)],
                "current_record": previous,
                "interaction_id": interaction_id,
            },
            config=config,
        )
    except Exception as e:
        print(f"[AGENT ERROR] agent_app.invoke failed: {e}")
        return {
            "aiReply": f"Sorry, I encountered an error: {str(e)}. Please try again.",
            "extractedData": None,
            "aiSuggestions": [],
        }

    # Extract the final state
    current_record = result.get("current_record")
    final_interaction_id = result.get("interaction_id")

    # Find the last AI text message
    ai_message = None
    try:
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                ai_message = msg.content
                break
    except Exception as e:
        print(f"[OUTPUT ERROR] Failed to extract AI message: {e}")

    if not ai_message:
        ai_message = "I've processed your request. Is there anything else you need?"

    # Save to database if there's a record
    try:
        if current_record and current_record.get("hcpName"):
            saved_id = save_interaction(current_record, thread_id, final_interaction_id)
            if saved_id and not final_interaction_id:
                final_interaction_id = saved_id
    except Exception as e:
        print(f"[DB ERROR] save_interaction failed: {e}")

    try:
        suggestions = _generate_suggestions(current_record or {})
    except Exception as e:
        print(f"[SUGGESTIONS ERROR] _generate_suggestions failed: {e}")
        suggestions = []

    print(f"[OUTGOING] aiReply: '{ai_message[:80]}...'")
    print(f"[OUTGOING] extractedData: {current_record}")
    print(f"[OUTGOING] aiSuggestions: {suggestions}")
    print(f"{'='*60}\n")

    return {
        "aiReply": ai_message,
        "extractedData": current_record,
        "aiSuggestions": suggestions,
    }
