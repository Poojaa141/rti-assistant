from agents.intent_agent import run_intent_agent
from agents.authority_agent import run_authority_agent
from agents.draft_agent import run_draft_agent
from agents.review_agent import run_review_agent
from agents.tracker_agent import run_tracker_agent

# ─────────────────────────────────────────
# CHANGE THIS NUMBER TO TEST DIFFERENT QUERIES
# 1 = Ration Card
# 2 = Passport
# 3 = Road/Pothole
# 4 = Pension
# 5 = Water Bill
# 6 = Aadhaar
# ─────────────────────────────────────────
TEST_NUMBER = 5

queries = {
    1: ("Pooja Patil",   "Pune, Maharashtra",    "I want to know why my ration card was rejected in Maharashtra"),
    2: ("Rahul Sharma",  "Mumbai, Maharashtra",  "My passport has been pending for 8 months in Mumbai"),
    3: ("Amit Kumar",    "New Delhi",            "The road near my house has potholes and has not been repaired for 2 years in Delhi"),
    4: ("Sunita Devi",   "Jaipur, Rajasthan",    "My pension application has been delayed for 6 months in Rajasthan"),
    5: ("Ramesh Patil",  "Chennai, Tamil Nadu",  "My water bill is incorrect and I am being overcharged in Chennai"),
    6: ("Priya Singh",   "Bangalore, Karnataka", "I want details of my Aadhaar update status which has been pending for 3 months"),
}

user_name, user_address, query = queries[TEST_NUMBER]

print("=" * 50)
print(f"TEST {TEST_NUMBER}: {query[:50]}...")
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
    print(f"WARNING: Draft review failed: {review['missing']}")

print("\nStep 5 - Saving and tracking...")
tracker = run_tracker_agent(user_name, user_address, intent, authority, draft)
print("[OK] Tracker:", tracker)

print("\n" + "=" * 50)
print("ALL 5 AGENTS WORKING SUCCESSFULLY!")
print("=" * 50)