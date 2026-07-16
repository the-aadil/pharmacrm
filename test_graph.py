# test_graph.py
from agent_graph import app
from langchain_core.messages import HumanMessage

def print_stream(stream):
    """Helper to cleanly print the graph execution stream."""
    for s in stream:
        for node, values in s.items():
            if "messages" in values:
                last_message = values["messages"][-1]
                # Print tool calls if they happen
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    print(f"\n[{node.upper()} ACTION] Calling Tool: {last_message.tool_calls[0]['name']}")
                # Print the final text response
                elif last_message.content:
                    print(f"\n[{node.upper()} RESPONSE]: {last_message.content}")

# Configure the session ID (maps to the 'chat_sessions' table in your DB schema)
config = {"configurable": {"thread_id": "session_001"}}

print("=== STARTING CONVERSATION ===")

# Turn 1: Rep logs the initial visit
turn_1_input = (
    "I just finished a 15 min visit with Dr. Smith. We talked about "
    "the new asthma inhaler, AeroBreathe. No samples given. Sentiment was neutral. "
    "Need to follow up next week."
)
print(f"\nREP: {turn_1_input}")
print_stream(app.stream({"messages": [HumanMessage(content=turn_1_input)]}, config=config))


# Turn 2: Rep corrects the record in the same thread
turn_2_input = (
    "Wait, I made a mistake. I actually gave him 2 samples from lot AB-123. "
    "Please update the record."
)
print(f"\nREP: {turn_2_input}")
print_stream(app.stream({"messages": [HumanMessage(content=turn_2_input)]}, config=config))