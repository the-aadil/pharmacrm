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
    duration_minutes: int = Field(default=30, description="Estimated duration of the meeting in minutes.")
    topics_discussed: str = Field(..., description="Deep, core technical summary of the medical/sales topics discussed.")
    sentiment: str = Field(..., description="The overall tone: 'positive', 'neutral', or 'negative'.")
    attendees: str = Field(default="", description="Additional people mentioned, comma separated. If none, return empty string.")
    date: str = Field(default="", description="Date of the interaction in YYYY-MM-DD format. If not mentioned, use today's date.")
    time: str = Field(default="", description="Time of the interaction in HH:MM 24-hour format. If not mentioned, use current time.")
    outcomes: str = Field(default="", description="Detailed summary of the meeting result or agreements. If not explicit, infer one logically.")
    products: List[ProductDiscussed] = Field(default_factory=list, description="List of products and samples detailed in the notes.")
    next_steps: Optional[str] = Field(None, description="Immediate tasks for the sales rep.")
    follow_ups: List[FollowUpAction] = Field(default_factory=list, description="Future calendar tasks or actions.")
    compliance_flag: bool = Field(default=False, description="Set to True if the notes mention ANY side effects, adverse events, or off-label application.")
    compliance_notes: Optional[str] = Field(None, description="Mandatory detailed notes explaining the compliance breach or medical concern.")
    ai_summary: str = Field(..., description="A 2-3 sentence executive summary of the encounter.")

# =====================================================================
# 2. INITIALIZE MODEL & IMPLEMENT THE LOG_INTERACTION TOOL
# =====================================================================

llm = ChatGroq(temperature=0.0, model_name="llama-3.1-8b-instant", max_retries=2, request_timeout=30)

@tool
def log_interaction(rep_notes: str) -> dict:
    """
    Parses unstructured sales representative notes into a strictly validated, 
    structured pharma CRM interaction record. Use this tool whenever a rep 
    summarizes a client interaction.
    """

    if not rep_notes or not rep_notes.strip():
        return {"status": "error", "message": "Please provide interaction notes to log."}

    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            f"TODAY: {today} TIME: {current_time}\n"
            "You are a CRM data extractor. Extract structured data from the rep's notes.\n"
            "Return ONLY a valid JSON object. No markdown, no explanation.\n\n"
            "REQUIRED fields:\n"
            "- hcp_name: Full name of the doctor/HCP. ALWAYS required. If the rep mentions a name, extract it. "
            "Capitalize properly (e.g. 'Dr. Zahir Shaikh'). If no name is mentioned, use 'Unknown HCP'.\n"
            "- interaction_type: One of 'visit', 'call', 'email', 'conference'. Default: 'visit'.\n"
            "- duration_minutes: Integer. Extract any duration mentioned. Default: 30.\n"
            "- topics_discussed: Summary of what was discussed. Default: 'General discussion'.\n"
            "- sentiment: One of 'positive', 'neutral', 'negative'. Default: 'neutral'.\n"
            "- ai_summary: 2-3 sentence executive summary.\n\n"
            "OPTIONAL fields:\n"
            "- attendees: Comma-separated names. Empty string if none.\n"
            "- date: YYYY-MM-DD format. Use today if not mentioned.\n"
            "- time: HH:MM 24-hour format. Use current time if not mentioned.\n"
            "- outcomes: Meeting outcomes. Infer if not explicit.\n"
            "- products: Array of objects with product_name (string), samples_given (int), lot_number (string or null).\n"
            "- next_steps: String or null.\n"
            "- follow_ups: Array of objects with due_date (YYYY-MM-DD string), note (string).\n"
            "- compliance_flag: Boolean. Set true if side effects, adverse events, or off-label use mentioned.\n"
            "- compliance_notes: String or null.\n\n"
            "Example input: 'Met Dr. Smith for 20 min, discussed Prodo-X, gave 5 samples, positive, follow up next week'\n"
            'Example output: {{"hcp_name": "Dr. Smith", "interaction_type": "visit", "duration_minutes": 20, ...}}'
        )),
        ("human", "{rep_notes}")
    ])

    try:
        raw_response = llm.invoke(prompt.format_messages(rep_notes=rep_notes))

        raw_text = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)

        # Strip markdown code fences if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        # === COMPREHENSIVE NORMALIZATION ===
        # Groq llama-3.1-8b-instant often returns wrong types and field names.
        # We must normalize everything before Pydantic validation.

        # 1. Coerce string-encoded arrays back to lists
        for field in ["products", "follow_ups", "next_steps", "outcomes", "attendees"]:
            val = parsed.get(field)
            if isinstance(val, str):
                try:
                    parsed[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    parsed[field] = val

        # 2. Normalize products array
        raw_products = parsed.get("products", [])
        if not isinstance(raw_products, list):
            raw_products = []
        fixed_products = []
        for p in raw_products:
            if isinstance(p, str):
                fixed_products.append({"product_name": p, "samples_given": 0, "lot_number": None})
            elif isinstance(p, dict):
                name = p.get("product_name") or p.get("name") or p.get("product") or "Unknown Product"
                samples = p.get("samples_given") or p.get("quantity") or p.get("samples") or 0
                lot = p.get("lot_number") or p.get("lot") or None
                fixed_products.append({"product_name": str(name), "samples_given": int(samples or 0), "lot_number": lot})
        parsed["products"] = fixed_products

        # 3. Normalize follow_ups array
        raw_followups = parsed.get("follow_ups", [])
        if not isinstance(raw_followups, list):
            raw_followups = []
        fixed_followups = []
        for f in raw_followups:
            if isinstance(f, str):
                fixed_followups.append({"due_date": today, "note": f})
            elif isinstance(f, dict):
                ddate = f.get("due_date") or f.get("date") or today
                note = f.get("note") or f.get("description") or f.get("action") or ""
                fixed_followups.append({"due_date": str(ddate), "note": str(note)})
        parsed["follow_ups"] = fixed_followups

        # 4. Normalize string fields that LLM might return as list/dict/None
        for field in ["attendees", "outcomes", "topics_discussed", "next_steps", "compliance_notes", "ai_summary"]:
            val = parsed.get(field)
            if isinstance(val, list):
                parsed[field] = ", ".join(str(v) for v in val) if val else ""
            elif isinstance(val, dict):
                parsed[field] = str(val.get("text", "") or val.get("summary", "") or "")
            elif val is None:
                parsed[field] = ""

        # 5. Normalize date/time - must be strings
        for field in ["date", "time"]:
            val = parsed.get(field)
            if val is None or val == "" or (isinstance(val, str) and val.lower() in ("not provided", "n/a", "unknown")):
                parsed[field] = today if field == "date" else current_time
            elif not isinstance(val, str):
                parsed[field] = str(val)

        # 6. Fix None/empty values for required fields
        if not parsed.get("duration_minutes"):
            parsed["duration_minutes"] = 30
        if not parsed.get("hcp_name"):
            parsed["hcp_name"] = "Unknown HCP"
        if not parsed.get("interaction_type"):
            parsed["interaction_type"] = "visit"
        if not parsed.get("topics_discussed"):
            parsed["topics_discussed"] = "General discussion"
        if not parsed.get("sentiment"):
            parsed["sentiment"] = "neutral"
        if not parsed.get("ai_summary"):
            parsed["ai_summary"] = "Interaction logged."

        # 7. Normalize interaction_type to valid values
        itype = str(parsed.get("interaction_type", "")).lower().strip()
        type_map = {
            "meeting": "visit", "visit": "visit", "in-person": "visit",
            "phone": "call", "telephone": "call", "call": "call",
            "email": "email", "mail": "email",
            "conference": "conference", "congress": "conference", "seminar": "conference",
        }
        parsed["interaction_type"] = type_map.get(itype, "visit")

        # 8. Normalize sentiment
        sent = str(parsed.get("sentiment", "")).lower().strip()
        sent_map = {"positive": "positive", "good": "positive", "great": "positive", "favorable": "positive",
                    "negative": "negative", "bad": "negative", "poor": "negative", "unfavorable": "negative"}
        parsed["sentiment"] = sent_map.get(sent, "neutral") if sent else "neutral"

        # 9. Normalize compliance_flag
        cf = parsed.get("compliance_flag")
        if isinstance(cf, str):
            parsed["compliance_flag"] = cf.lower() in ("true", "yes", "1")
        elif not isinstance(cf, bool):
            parsed["compliance_flag"] = False

        # 10. Normalize duration_minutes
        dm = parsed.get("duration_minutes")
        if isinstance(dm, str):
            try:
                parsed["duration_minutes"] = int(dm)
            except (ValueError, TypeError):
                parsed["duration_minutes"] = 30
        elif not isinstance(dm, int):
            parsed["duration_minutes"] = 30

        # 11. Remove HCP name from attendees
        attendees = parsed.get("attendees", "")
        hcp_name = parsed.get("hcp_name", "")
        if attendees and hcp_name:
            attendees_list = [a.strip() for a in str(attendees).split(",") if a.strip()]
            attendees_list = [a for a in attendees_list if a.lower() != hcp_name.lower()]
            parsed["attendees"] = ", ".join(attendees_list)

        # 12. Ensure ai_summary is not empty
        if not parsed.get("ai_summary") or parsed["ai_summary"] in ("Not Provided", "not provided"):
            parsed["ai_summary"] = f"Interaction with {parsed.get('hcp_name', 'HCP')} regarding {parsed.get('topics_discussed', 'general topics')}."

        record = ExtractedInteraction(**parsed).model_dump()

        return {
            "status": "pending_confirmation",
            "extracted_record": record,
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
def edit_interaction(current_record_json: dict, edit_request: str) -> dict:
    """
    Modifies an existing pending or saved CRM interaction based on a natural language request.
    It returns the updated record and an audit trail of the exact changes made.
    Writes audit trail to interaction_edit_history table atomically.
    """

    current_record_str = json.dumps(current_record_json)

    if not edit_request or not edit_request.strip():
        return {"status": "error", "message": "Please describe what you want to change."}

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a CRM data processor. Given a JSON record and a natural language edit request, "
            "apply the changes and return ONLY a JSON object with two keys:\n"
            "1. updated_record: the full updated record as a JSON object\n"
            "2. changes: an array of objects, each with field (string), old (string), new (string) for each changed field\n"
            "Do not modify unrelated fields. No explanation, no markdown.\n"
            "Examples of edit requests:\n"
            "- 'doctor name is John Smith' → update hcp_name to 'John Smith'\n"
            "- 'the name is Dr. Jane Doe' → update hcp_name to 'Dr. Jane Doe'\n"
            "- 'duration is 20 minutes' → update duration_minutes to 20\n"
            "- 'change sentiment to negative' → update sentiment to 'negative'\n"
            "- 'wrong name, it was actually Dr. Brown' → update hcp_name to 'Dr. Brown'"
        )),
        ("human", "Record:\n{current_record}\n\nEdit:\n{edit_request}")
    ])

    try:
        raw_response = llm.invoke(prompt.format_messages(current_record=current_record_str, edit_request=edit_request))
        raw_text = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        updated_record = parsed.get("updated_record", parsed)
        changes = parsed.get("changes", [])

        # Write audit trail to interaction_edit_history
        old_record = current_record_json if isinstance(current_record_json, dict) else json.loads(current_record_str)
        interaction_id = old_record.get("id")
        if interaction_id:
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                for change in changes:
                    field = change.get("field", "")
                    old_val = str(change.get("old", ""))
                    new_val = str(change.get("new", ""))
                    if old_val != new_val:
                        cursor.execute(
                            "INSERT INTO interaction_edit_history (interaction_id, edited_field, old_value, new_value) VALUES (?, ?, ?, ?)",
                            (interaction_id, field, old_val, new_val)
                        )
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                conn.close()

        return {
            "status": "updated",
            "updated_record": updated_record,
            "message": "Record updated."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Edit failed: {str(e)}"
        }

# =====================================================================
# 4. CONFIRM AND SAVE INTERACTION TOOL (DB COMMIT)
# =====================================================================

@tool
def confirm_and_save_interaction(final_record_json: dict) -> dict:
    """
    Commits a verified and approved interaction record into the CRM database.
    Use ONLY when the rep confirms the extracted data is correct.
    Input should be the complete extracted_record as a JSON object.
    """
    try:
        record = final_record_json

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
            record.get('duration_minutes'),
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