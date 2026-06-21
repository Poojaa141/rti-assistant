import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.intent_agent import run_intent_agent
from agents.authority_agent import run_authority_agent
from agents.draft_agent import run_draft_agent
from agents.review_agent import run_review_agent
from agents.tracker_agent import (
    run_tracker_agent,
    get_all_applications,
    get_dashboard_stats,
    update_application_status,
)
from database.pio_db import create_db

# Create FastAPI app
app = FastAPI(title="RTI Assistant API")
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")

# Allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins if origin.strip()],
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
    user_key: str | None = None

class StatusUpdateRequest(BaseModel):
    user_name: str
    user_key: str | None = None
    status: str

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
    tracker = run_tracker_agent(request.user_name, request.user_address, intent, authority, draft, request.user_key)
    
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

@app.get("/dashboard/{user_name}")
def get_dashboard(user_name: str):
    stats = get_dashboard_stats(user_name)
    return {
        "success": True,
        "stats": stats
    }

@app.patch("/my-rtis/{application_id}/status")
def update_my_rti_status(application_id: int, request: StatusUpdateRequest):
    result = update_application_status(
        application_id,
        request.user_name,
        request.status,
        request.user_key,
    )
    return result
