# test_tool.py
import json
from agent_tools import log_interaction

# Scenario A: Clean visit notes
sample_notes_clean = """Had a 20-minute discussion with Dr. Sarah Jenkins today at City General. She was highly enthusiastic (positive vibes) about our heart medication, Cardiorex. Handed over 5 samples from lot CR-9921. Scheduled an follow up for August 12th to review patient responses."""

# Scenario B: High-alert compliance event (Adverse event mentioned)
sample_notes_compliance = """Met Dr. Alex Kumar for a quick 10-minute catch up. He mentioned one of his elderly patients experienced severe dizziness and mild nausea after taking the new dosage of LipiSecure. He didn't want any samples today."""

def run_test(test_name, notes):
    print(f"\n--- Running Test: {test_name} ---")
    # Invoke our tool directly
    result = log_interaction.invoke({"rep_notes": notes})
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_test("Standard Clean Visit", sample_notes_clean)
    run_test("Adverse Event Compliance Trigger", sample_notes_compliance)