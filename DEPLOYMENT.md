# Deployment Guide

## Recommended 2-Day Deployment Plan

Use this safe setup:

- Frontend: Vercel, Netlify, or any static React hosting
- Backend: Render, Railway, or any Python web service
- Database: Supabase for RTI tracking/dashboard data
- Fallback: SQLite continues to work if Supabase is not configured

## Supabase Setup

1. Create a Supabase project.
2. Open SQL Editor.
3. Paste and run the SQL from `supabase_schema.sql`.
4. Copy your project URL.
5. Copy the `service_role` key for backend use only.

Never put the Supabase service role key in the frontend.

## Backend Environment Variables

Use these on the backend hosting service:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
FRONTEND_ORIGINS=https://your-frontend-domain.vercel.app
```

If Supabase variables are missing, the app uses SQLite automatically.

## Backend Commands

Install command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set the backend root directory to:

```text
backend
```

## Frontend Environment Variable

Use this on the frontend hosting service:

```text
REACT_APP_API_BASE_URL=https://your-backend-domain.onrender.com
```

Build command:

```text
npm run build
```

Publish directory:

```text
build
```

Set the frontend root directory to:

```text
frontend
```

## Presentation Line

This version is deployment-ready because it supports cloud storage through Supabase while keeping a local SQLite fallback for reliability during demos.
