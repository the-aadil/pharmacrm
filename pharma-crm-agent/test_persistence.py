# test_persistence.py
import sqlite3
import json
import os
from agent_graph import app
from langchain_core.messages import HumanMessage

def run_pipeline():
    config = {"configurable": {"thread_id": "session_003"}}
    
    turns = [
        "Log a 15 minute visit with Dr. Smith. Discussed AeroBreathe for asthma patients. He was positive. No samples given.",
        "Actually change that: I gave 3 samples from lot AB-777. And schedule a follow-up for next month.",
        "Perfect, everything looks exactly correct now. Please save this to the database."
    ]
    
    for i, user_input in enumerate(turns, 1):
        print(f"\n{'='*50}")
        print(f"[Turn {i}] Rep: {user_input}")
        print('='*50)
        
        stream = app.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            config=config
        )
        
        for s in stream:
            for node, values in s.items():
                if "messages" in values:
                    last_msg = values["messages"][-1]
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"  TOOL: {tc['name']}")
                    elif hasattr(last_msg, 'content') and last_msg.content:
                        print(f"  AI: {last_msg.content[:200]}")

    # Verify database
    print(f"\n{'='*50}")
    print("DATABASE VERIFICATION")
    print('='*50)
    
    db_path = os.path.join(os.path.dirname(__file__), "pharma_crm.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, hcp_name, duration_minutes, ai_summary FROM interactions ORDER BY id DESC LIMIT 1")
    interaction = cursor.fetchone()
    print(f"\nInteractions table (last row): {interaction}")
    
    if interaction:
        cursor.execute("SELECT product_name, samples_given, lot_number FROM interaction_products WHERE interaction_id=?", (interaction[0],))
        products = cursor.fetchall()
        print(f"Products: {products}")
        
        cursor.execute("SELECT due_date, note FROM follow_ups WHERE interaction_id=?", (interaction[0],))
        followups = cursor.fetchall()
        print(f"Follow-ups: {followups}")
    
    conn.close()
    
    print(f"\n{'='*50}")
    if interaction and products:
        print("PERSISTENCE PIPELINE: SUCCESS")
    else:
        print("PERSISTENCE PIPELINE: FAILED")

if __name__ == "__main__":
    run_pipeline()