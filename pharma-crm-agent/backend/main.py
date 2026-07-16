# backend/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent_graph import app

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
                    tools_called.append(tc.get("name", "unknown"))

        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and msg.type == "ai":
                reply = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        return ChatResponse(
            reply=reply or "Processing complete.",
            extracted_data=extracted_data,
            tools_called=tools_called,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from backend.routes import router
api.include_router(router)
