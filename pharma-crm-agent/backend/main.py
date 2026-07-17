# backend/main.py
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent_graph import app

TOOL_NAMES = [
    "log_interaction", "edit_interaction", "confirm_and_save_interaction",
    "search_hcp", "get_hcp_briefing", "suggest_next_best_action",
    "schedule_follow_up", "get_upcoming_appointments", "search_articles"
]

def _clean_reply(text: str) -> str:
    """Strip leaked tool names from AI reply text."""
    if not text:
        return text
    cleaned = text
    for name in TOOL_NAMES:
        cleaned = re.sub(rf'\b{re.escape(name)}[\s]*[\(:]?', '', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    reply: str
    extracted_data: dict = {}
    tools_called: list = []
    status: str = "ok"

api = FastAPI(title="Pharma CRM Agent API", version="1.0.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
def root():
    return {"status": "ok", "message": "Pharma CRM Agent API running"}

@api.get("/health")
def health():
    return {"status": "healthy"}

@api.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        if not request.message or not request.message.strip():
            return ChatResponse(reply="Please type a message.", status="error")
        if len(request.message) > 5000:
            return ChatResponse(reply="Message too long. Please keep it under 5000 characters.", status="error")

        config = {"configurable": {"thread_id": request.thread_id}}
        result = app.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        messages = result.get("messages", [])
        reply = ""
        tools_called = []
        extracted_data = result.get("extracted_record") or {}
        pending = result.get("pending_confirmation", False)
        status = "pending_confirmation" if pending else "ok"

        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    if name not in tools_called:
                        tools_called.append(name)

        for msg in reversed(messages):
            msg_type = getattr(msg, "type", None)
            content = getattr(msg, "content", None)
            has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
            if msg_type == "ai" and content and not has_tool_calls:
                reply = content if isinstance(content, str) else str(content)
                break

        reply = _clean_reply(reply) or "Processing complete."

        return ChatResponse(
            reply=reply,
            extracted_data=extracted_data,
            tools_called=tools_called,
            status=status
        )
    except Exception as e:
        return ChatResponse(reply="Something went wrong. Please try again.", status="error")

from backend.routes import router
api.include_router(router)
