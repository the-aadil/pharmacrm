# backend/routes.py
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent_tools import (
    log_interaction, edit_interaction,
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
        record = json.loads(request.record_json)
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interactions
            (hcp_name, interaction_type, duration_minutes, topics_discussed,
             sentiment, next_steps, ai_summary, compliance_flag, compliance_notes,
             interaction_date, interaction_time, attendees, outcomes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('hcp_name'),
            record.get('interaction_type'),
            record.get('duration_minutes', 30),
            record.get('topics_discussed'),
            record.get('sentiment'),
            record.get('next_steps'),
            record.get('ai_summary'),
            1 if record.get('compliance_flag') else 0,
            record.get('compliance_notes'),
            record.get('date'),
            record.get('time'),
            record.get('attendees'),
            record.get('outcomes')
        ))

        interaction_id = cursor.lastrowid

        for prod in record.get('products', []):
            cursor.execute(
                "INSERT INTO interaction_products (interaction_id, product_name, samples_given, lot_number) VALUES (?, ?, ?, ?)",
                (interaction_id, prod.get('product_name'), prod.get('samples_given', 0), prod.get('lot_number'))
            )

        for followup in record.get('follow_ups', []):
            cursor.execute(
                "INSERT INTO follow_ups (interaction_id, hcp_name, due_date, note) VALUES (?, ?, ?, ?)",
                (interaction_id, record.get('hcp_name'), followup.get('due_date'), followup.get('note'))
            )

        conn.commit()
        conn.close()

        return {"status": "committed_to_db", "interaction_id": interaction_id, "message": f"Interaction #{interaction_id} saved successfully."}
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
