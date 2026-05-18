from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.intent_agent import run_intent_agent
from agents.authority_agent import run_authority_agent
from agents.draft_agent import run_draft_agent
from agents.review_agent import run_review_agent
from agents.tracker_agent import run_tracker_agent, get_all_applications
from database.pio_db import create_db

# Create FastAPI app
app = FastAPI(title="RTI Assistant API")

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database on startup
create_db()

# This defines what data React will send us
class RTIRequest(BaseModel):
    query: str
    user_name: str
    user_address: str

# ─────────────────────────────────────────
# Endpoint 1 — Health check
# ─────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "RTI Assistant is running!"}

# ─────────────────────────────────────────
# Endpoint 2 — Generate RTI
# ─────────────────────────────────────────
@app.post("/generate-rti")
def generate_rti(request: RTIRequest):
    
    # Step 1 - Understand the query
    intent = run_intent_agent(request.query)
    
    # Step 2 - Find government office
    authority = run_authority_agent(intent)
    
    # Step 3 - Write RTI letter
    draft = run_draft_agent(intent, authority, request.user_name, request.user_address)
    
    # Step 4 - Review the draft
    review = run_review_agent(draft)
    
    # Step 5 - Save and track
    tracker = run_tracker_agent(request.user_name, request.user_address, intent, authority, draft)
    
    return {
        "success": True,
        "intent": intent,
        "authority": authority,
        "draft": draft,
        "review": review,
        "tracker": tracker
    }

# ─────────────────────────────────────────
# Endpoint 3 — Get all RTI applications
# ─────────────────────────────────────────
@app.get("/my-rtis/{user_name}")
def get_my_rtis(user_name: str):
    applications = get_all_applications(user_name)
    return {
        "success": True,
        "applications": applications
    }