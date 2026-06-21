# Agentic AI-Based RTI Assistant

This project is an Agentic AI-based RTI and citizen issue management system.

Users describe a public service issue, and multiple AI agents work together to:

- understand the citizen query
- detect the correct department
- find the public authority or PIO
- generate a formal RTI draft
- review the draft quality
- track deadline and status
- show dashboard analytics

## Current Tech Stack

- React
- FastAPI
- Python
- Groq/Llama AI
- SQLite local fallback
- Optional Supabase cloud tracking
- Supabase Auth for citizen login
- Axios

## Agentic AI Workflow

1. Intent Agent
2. Authority Agent
3. Drafting Agent
4. Review Agent
5. Tracking Agent

## Advanced Features

- Dashboard analytics
- My RTIs tracking page
- Status update lifecycle
- Priority badges
- Department analytics
- Optional Supabase database support
- Authenticated citizen accounts

## Supabase Auth

The frontend uses Supabase email/password authentication. Add these values in `frontend/.env`:

```text
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your_publishable_or_anon_key
```

Each RTI is saved using the authenticated user's unique Supabase user ID, so citizens with the same name or address do not share records.

## Run Locally

Backend:

```text
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:

```text
cd frontend
npm install
npm start
```

Open:

```text
http://localhost:3000
```
