from agents.intent_agent import run_intent_agent
from agents.authority_agent import run_authority_agent
from agents.draft_agent import run_draft_agent
from agents.review_agent import run_review_agent
from agents.tracker_agent import run_tracker_agent


user_name = "Pooja Patil"
user_address = "Pune, Maharashtra"
query = "I want to know why my ration card was rejected in Maharashtra"

print("=" * 50)
print("RTI ASSISTANT - FULL PIPELINE TEST")
print("=" * 50)

print("\nStep 1 - Understanding your query...")
intent = run_intent_agent(query)
print("[OK] Intent:", intent)

print("\nStep 2 - Finding government office...")
authority = run_authority_agent(intent)
print("[OK] Authority:", authority)

print("\nStep 3 - Writing RTI application...")
draft = run_draft_agent(intent, authority, user_name, user_address)
print("[OK] Draft written successfully!")
print("\n--- RTI LETTER ---")
print(draft)

print("\nStep 4 - Reviewing RTI draft...")
review = run_review_agent(draft)
print("[OK] Review:", review)
if not review["passed"]:
    raise ValueError(f"Draft review failed: {review['missing']}")

print("\nStep 5 - Saving and tracking...")
tracker = run_tracker_agent(user_name, user_address, intent, authority, draft)
print("[OK] Tracker:", tracker)

print("\n" + "=" * 50)
print("ALL 5 AGENTS WORKING SUCCESSFULLY!")
print("=" * 50)
