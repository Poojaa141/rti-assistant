from agents.intent_agent import run_intent_agent
from agents.authority_agent import run_authority_agent

query = "I want to know why my ration card was rejected in Maharashtra"

print("Step 1 - Agent 1 understanding your query...")
intent = run_intent_agent(query)
print("Result:", intent)

print("\nStep 2 - Agent 2 finding the right government office...")
authority = run_authority_agent(intent)
print("Result:", authority)

print("\nBoth agents working together successfully!")