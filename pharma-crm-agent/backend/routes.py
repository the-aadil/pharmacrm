# backend/routes.py
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent_tools import (
    log_interaction, edit_interaction, confirm_and_save_interaction,
    search_hcp, get_hcp_briefing, suggest_next_best_action, schedule_follow_up,
    get_upcoming_appointments, search_articles, get_db_path
)

router = APIRouter()

class FormRequest(BaseModel):
    rep_notes: str

class ConfirmRequest(BaseModel):
    record_json: str

class EditRequest(BaseModel):
    interaction_id: int
    change_request: str

class FollowUpRequest(BaseModel):
    hcp_name: str
    due_description: str
    note: str

@router.post("/api/interactions")
def create_interaction(request: FormRequest):
    try:
        result = log_interaction.invoke({"rep_notes": request.rep_notes})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/interactions/confirm")
def confirm_interaction(request: ConfirmRequest):
    try:
        result = confirm_and_save_interaction.invoke({"final_record_json": request.record_json})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/interactions/{interaction_id}")
def edit_interaction_endpoint(interaction_id: int, request: EditRequest):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interactions WHERE id = ?", (interaction_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Interaction {interaction_id} not found")
        record = dict(zip(columns, row))
        result = edit_interaction.invoke({
            "current_record_json": json.dumps(record),
            "edit_request": request.change_request
        })
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/hcps")
def search_hcps(query: str):
    try:
        result = search_hcp.invoke({"query": query})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/hcps/{hcp_name}/briefing")
def hcp_briefing(hcp_name: str):
    try:
        result = get_hcp_briefing.invoke({"hcp_name": hcp_name})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/hcps/{hcp_name}/suggestions")
def hcp_suggestions(hcp_name: str):
    try:
        result = suggest_next_best_action.invoke({"hcp_name": hcp_name})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/followups")
def create_followup(request: FollowUpRequest):
    try:
        result = schedule_follow_up.invoke({
            "hcp_name": request.hcp_name,
            "due_description": request.due_description,
            "note": request.note
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/appointments")
def get_appointments(rep_name: str = "current user"):
    try:
        result = get_upcoming_appointments.invoke({"rep_name": rep_name})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/articles")
def search_articles_endpoint(query: str):
    try:
        result = search_articles.invoke({"query": query})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
