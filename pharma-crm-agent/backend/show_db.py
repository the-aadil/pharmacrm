from backend.database import SessionLocal
from backend.models import Interaction

db = SessionLocal()
records = db.query(Interaction).order_by(Interaction.id.desc()).all()
db.close()

header = f"{'ID':<4} | {'HCP Name':<22} | {'Type':<10} | {'Dur':<5} | {'Sentiment':<10} | {'Topics':<30} | {'Attendees':<22} | {'Outcomes':<30} | {'Follow-ups':<30} | {'Thread':<18}"
print(header)
print("-" * len(header))
for r in records:
    topics = (r.topics_discussed or "")[:30]
    attendees = (r.attendees or "")[:22]
    outcomes = (r.outcomes or "")[:30]
    followups = (r.follow_up_actions or "")[:30]
    thread = (r.thread_id or "")[:18]
    print(f"{r.id:<4} | {(r.hcp_name or ''):<22} | {(r.interaction_type or ''):<10} | {str(r.duration or 0)+'m':<5} | {(r.sentiment or ''):<10} | {topics:<30} | {attendees:<22} | {outcomes:<30} | {followups:<30} | {thread:<18}")
