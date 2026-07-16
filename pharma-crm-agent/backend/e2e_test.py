import sys
sys.path.insert(0, '.')
from langgraph_agent import run_agent
import sqlite3

msg = ("I just concluded a call with Dr. Sarah Jenkins from the oncology department. "
       "We spent 55 minutes reviewing the adverse event data from the Phase 2 trials of Drug Z. "
       "She expressed serious concerns about the liver toxicity findings and wants to see the "
       "pediatric safety data before she will consider prescribing it. "
       "I agreed to email the pediatric safety packet to her by Friday.")

r = run_agent(msg, 'full_e2e_test')

print('=== aiReply ===')
print(r['aiReply'])
print()
print('=== extractedData ===')
for k, v in r['extractedData'].items():
    print(f'  {k}: {v}')
print()
print('=== aiSuggestions ===')
for s in r['aiSuggestions']:
    print(f'  - {s}')

print()
print('=== DATABASE CHECK ===')
conn = sqlite3.connect('C:/Users/Administrator/Desktop/pharmacrm/pharma_crm.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM interactions')
print(f'Total rows: {c.fetchone()[0]}')
c.execute('SELECT id, hcp_name, interaction_type, duration, sentiment, topics_discussed, attendees, outcomes, follow_up_actions, thread_id FROM interactions ORDER BY id DESC LIMIT 3')
for row in c.fetchall():
    print(f'  ID:{row[0]} | {row[1]} | {row[2]} | {row[3]}m | {row[4]} | topics:{row[5]} | attendees:{row[6]} | outcomes:{row[7]} | followups:{row[8]} | thread:{row[9]}')
conn.close()
