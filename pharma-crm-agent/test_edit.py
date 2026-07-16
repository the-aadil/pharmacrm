import json
from agent_tools import edit_interaction

current_pending_record = {
    "hcp_name": "Dr. Sarah Jenkins",
    "interaction_type": "visit",
    "duration_minutes": 20,
    "topics_discussed": "Discussed Cardiorex. Handed over samples.",
    "sentiment": "positive",
    "products": [
        {
            "product_name": "Cardiorex",
            "samples_given": 5,
            "lot_number": "CR-9921"
        }
    ],
    "next_steps": "Follow up in August.",
    "follow_ups": [],
    "compliance_flag": False,
    "compliance_notes": None,
    "ai_summary": "Met with Dr. Jenkins regarding Cardiorex. Provided 5 samples."
}

rep_correction = "Actually, I only gave her 3 samples, and the meeting was 30 minutes long."

print("--- Running Edit Tool ---")

result = edit_interaction.invoke({
    "current_record_json": json.dumps(current_pending_record),
    "edit_request": rep_correction
})

print(json.dumps(result, indent=2))
