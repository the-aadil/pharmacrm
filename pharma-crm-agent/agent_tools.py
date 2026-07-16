# agent_tools.py
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_path():
    """Get database path from environment or fallback to local SQLite."""
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and "sqlite:///" in db_url:
        return db_url.replace("sqlite:///", "")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "pharma_crm.db")

# =====================================================================
# 1. DEFINE PYDANTIC SCHEMA FOR STRUCTURED OUTPUT
# =====================================================================

class ProductDiscussed(BaseModel):
    product_name: str = Field(..., description="Name of the pharmaceutical product discussed.")
    samples_given: int = Field(default=0, description="Number of samples provided to the HCP.")
    lot_number: Optional[str] = Field(None, description="Lot number of the distributed samples.")

class FollowUpAction(BaseModel):
    due_date: str = Field(..., description="ISO format date (YYYY-MM-DD) for when the action is due.")
    note: str = Field(..., description="Specific action items or tasks required.")

class ExtractedInteraction(BaseModel):
    hcp_name: str = Field(..., description="Full name of the Healthcare Professional.")
    interaction_type: str = Field(..., description="Type of interaction. Must be 'visit', 'call', 'email', or 'conference'.")
    duration_minutes: int = Field(..., description="Estimated duration of the meeting in minutes.")
    topics_discussed: str = Field(..., description="Deep, core technical summary of the medical/sales topics discussed.")
    sentiment: str = Field(..., description="The overall tone: 'positive', 'neutral', or 'negative'.")
    products: List[ProductDiscussed] = Field(default_factory=list, description="List of products and samples detailed in the notes.")
    next_steps: Optional[str] = Field(None, description="Immediate tasks for the sales rep.")
    follow_ups: List[FollowUpAction] = Field(default_factory=list, description="Future calendar tasks or actions.")
    compliance_flag: bool = Field(default=False, description="Set to True if the notes mention ANY side effects, adverse events, or off-label application.")
    compliance_notes: Optional[str] = Field(None, description="Mandatory detailed notes explaining the compliance breach or medical concern.")
    ai_summary: str = Field(..., description="A 2-3 sentence executive summary of the encounter.")

# =====================================================================
# 2. INITIALIZE MODEL & IMPLEMENT THE LOG_INTERACTION TOOL
# =====================================================================

llm = ChatGroq(temperature=0.0, model_name="llama-3.1-8b-instant")

@tool
def log_interaction(rep_notes: str) -> dict:
    """
    Parses unstructured sales representative notes into a strictly validated, 
    structured pharma CRM interaction record. Use this tool whenever a rep 
    summarizes a client interaction.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert compliance officer and data architect for a global pharmaceutical firm.\n"
            "Analyze the unstructured text provided by the sales representative and map it perfectly to the required output schema.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "- The products field MUST be a JSON array of objects, not a string.\n"
            "- The follow_ups field MUST be a JSON array of objects, not a string.\n"
            "- If no products are mentioned, use an empty array.\n"
            "- If no follow-ups are mentioned, use an empty array.\n\n"
            "STRICT COMPLIANCE RULE: If the representative mentions any side effects, patient complaints, adverse reactions, "
            "or off-label use cases, you MUST set compliance_flag to true and provide a thorough clinical report inside compliance_notes."
        )),
        ("human", "{rep_notes}")
    ])

    # Force the model to output JSON that strictly matches our Pydantic schema
    structured_llm = llm.with_structured_output(ExtractedInteraction)
    chain = prompt | structured_llm

    try:
        extracted_data = chain.invoke({"rep_notes": rep_notes})

        # Structure the response for a Human-in-the-Loop review state
        return {
            "status": "pending_confirmation",
            "extracted_record": extracted_data.model_dump(),
            "message": "Data extracted successfully. Awaiting human confirmation before CRM commit."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Data extraction routine failed: {str(e)}"
        }

# =====================================================================
# 3. EDIT INTERACTION TOOL WITH AUDIT TRAIL
# =====================================================================

class AuditEntry(BaseModel):
    """A single audit trail entry tracking what changed."""
    edited_field: str = Field(..., description="Name of the field that was changed")
    old_value: str = Field(..., description="Previous value before edit")
    new_value: str = Field(..., description="New value after edit")

class EditResult(BaseModel):
    """Result of an edit operation with updated record and audit trail."""
    updated_record: dict = Field(..., description="The complete updated interaction record")
    audit_trail: List[AuditEntry] = Field(default_factory=list, description="List of changes made")

@tool
def edit_interaction(current_record_json: str, edit_request: str) -> dict:
    """
    Modifies an existing pending or saved CRM interaction based on a natural language request.
    It returns the updated record and an audit trail of the exact changes made.
    Writes audit trail to interaction_edit_history table atomically.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a pharmaceutical CRM data processor. You will be provided with a JSON representation "
            "of a current interaction record, and a natural language request from the sales rep to change it.\n\n"
            "Your tasks:\n"
            "1. Apply the requested changes to the record accurately.\n"
            "2. Return the ENTIRE updated record.\n"
            "3. Generate an exact audit trail detailing which fields changed, including the old and new values.\n"
            "Do not modify fields that are not related to the edit request."
        )),
        ("human", "Current Record:\n{current_record}\n\nRequested Edit:\n{edit_request}")
    ])

    structured_llm = llm.with_structured_output(EditResult)
    chain = prompt | structured_llm

    try:
        edit_data = chain.invoke({
            "current_record": current_record_json,
            "edit_request": edit_request
        })

        updated_record = edit_data.updated_record if isinstance(edit_data.updated_record, dict) else edit_data.updated_record.model_dump()

        # Write audit trail to interaction_edit_history
        old_record = json.loads(current_record_json)
        interaction_id = old_record.get("id")
        if interaction_id:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                for field in ["hcp_name", "interaction_type", "duration_minutes", "topics_discussed",
                              "sentiment", "next_steps"]:
                    old_val = str(old_record.get(field, ""))
                    new_val = str(updated_record.get(field, ""))
                    if old_val != new_val:
                        cursor.execute(
                            "INSERT INTO interaction_edit_history (interaction_id, edited_field, old_value, new_value) VALUES (?, ?, ?, ?)",
                            (interaction_id, field, old_val, new_val)
                        )

                old_products = old_record.get("products", [])
                new_products = updated_record.get("products", [])
                if old_products != new_products:
                    cursor.execute(
                        "INSERT INTO interaction_edit_history (interaction_id, edited_field, old_value, new_value) VALUES (?, ?, ?, ?)",
                        (interaction_id, "products", json.dumps(old_products), json.dumps(new_products))
                    )

                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        return {
            "status": "updated",
            "updated_record": updated_record,
            "audit_trail": [audit.model_dump() for audit in edit_data.audit_trail],
            "message": "Record updated. Audit trail generated."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Edit extraction failed: {str(e)}"
        }

# =====================================================================
# 4. CONFIRM AND SAVE INTERACTION TOOL (DB COMMIT)
# =====================================================================

@tool
def confirm_and_save_interaction(final_record_json: str) -> dict:
    """
    Commits a verified and approved interaction record into the CRM database.
    Use ONLY when the rep confirms the extracted data is correct.
    Input should be a JSON string of the extracted_record.
    """
    try:
        record = json.loads(final_record_json)

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interactions 
            (hcp_name, interaction_type, duration_minutes, topics_discussed, 
             sentiment, next_steps, ai_summary, compliance_flag, compliance_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get('hcp_name'),
            record.get('interaction_type'),
            record.get('duration_minutes'),
            record.get('topics_discussed'),
            record.get('sentiment'),
            record.get('next_steps'),
            record.get('ai_summary'),
            1 if record.get('compliance_flag') else 0,
            record.get('compliance_notes')
        ))
        
        interaction_id = cursor.lastrowid
        
        for prod in record.get('products', []):
            cursor.execute("""
                INSERT INTO interaction_products 
                (interaction_id, product_name, samples_given, lot_number)
                VALUES (?, ?, ?, ?)
            """, (interaction_id, prod.get('product_name'),
                   prod.get('samples_given', 0), prod.get('lot_number')))

        for followup in record.get('follow_ups', []):
            cursor.execute("""
                INSERT INTO follow_ups (interaction_id, hcp_name, due_date, note)
                VALUES (?, ?, ?, ?)
            """, (interaction_id, record.get('hcp_name'),
                   followup.get('due_date'), followup.get('note')))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "committed_to_db",
            "interaction_id": interaction_id,
            "message": f"Interaction #{interaction_id} saved successfully."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database insert failed: {str(e)}"
        }

# =====================================================================
# 5. SEARCH HCP TOOL
# =====================================================================

@tool
def search_hcp(query: str) -> dict:
    """
    Search HCPs by name or specialty. Returns matching profiles from the database.
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, specialty FROM hcps WHERE LOWER(name) LIKE ? OR LOWER(specialty) LIKE ?",
            (f"%{query.lower()}%", f"%{query.lower()}%")
        )
        results = cursor.fetchall()
        conn.close()
        
        hcps = [{"id": r[0], "name": r[1], "specialty": r[2]} for r in results]
        
        if len(hcps) == 0:
            return {"status": "no_results", "hcps": [], "message": f"No HCPs matching '{query}'."}
        elif len(hcps) == 1:
            return {"status": "single_match", "hcps": hcps, "message": "Found 1 HCP."}
        else:
            return {"status": "multiple_matches", "hcps": hcps, "count": len(hcps), "message": f"Found {len(hcps)} HCPs."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 6. GET HCP BRIEFING TOOL
# =====================================================================

@tool
def get_hcp_briefing(hcp_name: str) -> dict:
    """
    Get pre-visit briefing: HCP profile, recent interactions, open follow-ups, AI summary.
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, specialty FROM hcps WHERE LOWER(name) = ?", (hcp_name.lower(),))
        hcp = cursor.fetchone()
        if not hcp:
            conn.close()
            return {"status": "not_found", "message": f"HCP '{hcp_name}' not found."}
        
        cursor.execute(
            "SELECT id, interaction_type, duration_minutes, topics_discussed, sentiment, ai_summary, created_at FROM interactions WHERE LOWER(hcp_name) = ? ORDER BY created_at DESC LIMIT 5",
            (hcp_name.lower(),)
        )
        interactions = cursor.fetchall()
        
        cursor.execute(
            "SELECT id, due_date, note FROM follow_ups WHERE LOWER(hcp_name) = ? AND status='open' ORDER BY due_date ASC",
            (hcp_name.lower(),)
        )
        followups = cursor.fetchall()
        conn.close()
        
        recent = [{"id": r[0], "type": r[1], "duration": r[2], "topics": r[3], "sentiment": r[4], "summary": r[5], "date": r[6]} for r in interactions]
        open_f = [{"id": f[0], "due_date": f[1], "note": f[2]} for f in followups]
        
        prompt = f"""Create a 3-4 sentence pre-visit briefing for:
HCP: {hcp[1]} ({hcp[2]})
Recent: {json.dumps(recent)}
Follow-ups: {json.dumps(open_f)}
Include relationship status, key topics, open items, and suggested approach."""
        
        msg = llm.invoke(prompt)
        briefing = msg.content if hasattr(msg, 'content') else str(msg)
        
        return {"status": "success", "hcp": {"id": hcp[0], "name": hcp[1], "specialty": hcp[2]}, "recent": recent, "follow_ups": open_f, "briefing": briefing}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 7. SUGGEST NEXT BEST ACTION TOOL
# =====================================================================

@tool
def suggest_next_best_action(hcp_name: str) -> dict:
    """
    Analyze HCP history and suggest 3-5 next best actions for the upcoming visit.
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, specialty FROM hcps WHERE LOWER(name) = ?", (hcp_name.lower(),))
        hcp = cursor.fetchone()
        if not hcp:
            conn.close()
            return {"status": "not_found", "message": f"HCP '{hcp_name}' not found."}
        
        cursor.execute(
            "SELECT ai_summary, sentiment FROM interactions WHERE LOWER(hcp_name) = ? ORDER BY created_at DESC LIMIT 10",
            (hcp_name.lower(),)
        )
        history = cursor.fetchall()
        
        cursor.execute(
            "SELECT DISTINCT ip.product_name, SUM(ip.samples_given) FROM interaction_products ip JOIN interactions i ON ip.interaction_id = i.id WHERE LOWER(i.hcp_name) = ? GROUP BY ip.product_name",
            (hcp_name.lower(),)
        )
        products = cursor.fetchall()
        conn.close()
        
        hist_text = "\n".join([f"- [{r[1]}] {r[0]}" for r in history]) or "No history"
        prod_text = "\n".join([f"- {p[0]} ({p[1]} samples)" for p in products]) or "None"
        
        prompt = f"""Suggest 3-5 next actions for:
HCP: {hcp[1]} ({hcp[2]})
History: {hist_text}
Products: {prod_text}
Return numbered list with brief reasoning."""
        
        msg = llm.invoke(prompt)
        suggestions = msg.content if hasattr(msg, 'content') else str(msg)
        
        return {"status": "success", "hcp": hcp[1], "total_visits": len(history), "products": [{"name": p[0], "samples": p[1]} for p in products], "suggestions": suggestions}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 8. SCHEDULE FOLLOW-UP TOOL
# =====================================================================

@tool
def schedule_follow_up(hcp_name: str, due_description: str, note: str) -> dict:
    """
    Schedule a follow-up. Parses natural language dates like 'next Tuesday', 'in 2 weeks'.
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM hcps WHERE LOWER(name) = ?", (hcp_name.lower(),))
        hcp = cursor.fetchone()
        if not hcp:
            conn.close()
            return {"status": "not_found", "message": f"HCP '{hcp_name}' not found."}
        
        today = datetime.now()
        prompt = f"Today is {today.strftime('%Y-%m-%d')} ({today.strftime('%A')}). Convert this to YYYY-MM-DD: '{due_description}'. Return ONLY the date."
        msg = llm.invoke(prompt)
        parsed = (msg.content if hasattr(msg, 'content') else str(msg)).strip()
        
        try:
            due = datetime.strptime(parsed, "%Y-%m-%d")
            if due.date() <= today.date():
                parsed = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        except:
            parsed = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        cursor.execute("INSERT INTO follow_ups (hcp_name, due_date, note, status) VALUES (?, ?, ?, 'open')", (hcp[1], parsed, note))
        fid = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"status": "scheduled", "id": fid, "hcp": hcp[1], "due_date": parsed, "note": note}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 9. GET UPCOMING APPOINTMENTS TOOL (MOCK)
# =====================================================================

@tool
def get_upcoming_appointments(rep_name: str = "current user") -> dict:
    """
    Get a list of upcoming appointments for the sales rep. Returns mock data.
    """
    try:
        today = datetime.now()
        mock_appointments = [
            {"hcp_name": "Dr. Sarah Chen", "specialty": "Cardiology", "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "time": "10:00 AM", "location": "City Hospital"},
            {"hcp_name": "Dr. James Wilson", "specialty": "Neurology", "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "time": "2:00 PM", "location": "Medical Center"},
            {"hcp_name": "Dr. Emily Rodriguez", "specialty": "Pediatrics", "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "time": "11:30 AM", "location": "Children's Clinic"},
        ]
        return {
            "status": "success",
            "rep_name": rep_name,
            "appointments": mock_appointments,
            "count": len(mock_appointments)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# =====================================================================
# 10. SEARCH ARTICLES TOOL (MOCK)
# =====================================================================

@tool
def search_articles(query: str) -> dict:
    """
    Search medical/pharma articles relevant to the given query. Returns mock results.
    """
    try:
        mock_results = [
            {"title": f"Recent advances in {query}", "journal": "New England Journal of Medicine", "date": "2026-06-15", "summary": f"A comprehensive study on {query} and treatment outcomes."},
            {"title": f"Clinical trial results for {query}", "journal": "The Lancet", "date": "2026-05-20", "summary": f"Phase III trial showing efficacy of new {query} therapies."},
            {"title": f"{query} in practice", "journal": "Journal of Clinical Pharmacology", "date": "2026-04-10", "summary": f"Practical guidelines for integrating {query} into patient care."},
        ]
        return {
            "status": "success",
            "query": query,
            "articles": mock_results,
            "count": len(mock_results)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}