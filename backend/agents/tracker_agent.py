import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_TABLE = "rti_applications"


def use_supabase() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def supabase_headers(prefer_return: bool = False) -> dict:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer_return:
        headers["Prefer"] = "return=representation"
    return headers


def supabase_endpoint() -> str:
    return urljoin(f"{SUPABASE_URL}/", f"rest/v1/{SUPABASE_TABLE}")

def init_tracker_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rti_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT,
            user_name TEXT,
            user_address TEXT,
            subject TEXT,
            department TEXT,
            pio_name TEXT,
            pio_address TEXT,
            state TEXT,
            draft TEXT,
            filed_date TEXT,
            deadline_date TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    cur.execute("PRAGMA table_info(rti_applications)")
    columns = {row[1] for row in cur.fetchall()}
    if "user_key" not in columns:
        cur.execute("ALTER TABLE rti_applications ADD COLUMN user_key TEXT")
    conn.commit()
    conn.close()

def run_tracker_agent(user_name: str, user_address: str, intent: dict, authority: dict, draft: str, user_key: str | None = None) -> dict:
    filed_date = datetime.now().strftime("%Y-%m-%d")
    deadline_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    days_remaining = 30

    if use_supabase():
        try:
            return run_supabase_tracker_agent(
                user_name,
                user_address,
                intent,
                authority,
                draft,
                user_key,
                filed_date,
                deadline_date,
                days_remaining,
            )
        except Exception as error:
            print(f"Supabase tracker failed, using SQLite fallback: {error}")

    init_tracker_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rti_applications
        (user_key, user_name, user_address, subject, department, pio_name, pio_address, state, draft, filed_date, deadline_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_key,
        user_name,
        user_address,
        intent["subject"],
        authority["department"],
        authority["pio_name"],
        authority["address"],
        intent["state"],
        draft,
        filed_date,
        deadline_date,
        "Pending"
    ))
    conn.commit()
    application_id = cur.lastrowid
    conn.close()

    return {
        "application_id": application_id,
        "filed_date": filed_date,
        "deadline_date": deadline_date,
        "days_remaining": days_remaining,
        "status": "Pending",
        "message": f"RTI saved! Government must respond by {deadline_date} (30 days)"
    }

def get_all_applications(user_name: str) -> list:
    lookup_key = normalize_lookup_key(user_name)
    if use_supabase():
        try:
            return get_supabase_applications(user_name, lookup_key)
        except Exception as error:
            print(f"Supabase dashboard read failed, using SQLite fallback: {error}")

    init_tracker_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, subject, department, pio_name, state, filed_date, deadline_date, status, draft
        FROM rti_applications
        WHERE user_key = ? OR (user_key IS NULL AND user_name = ?)
        ORDER BY filed_date DESC
    """, (lookup_key, user_name))
    rows = cur.fetchall()
    conn.close()

    applications = []
    for row in rows:
        filed = datetime.strptime(row[5], "%Y-%m-%d")
        deadline = datetime.strptime(row[6], "%Y-%m-%d")
        days_remaining = (deadline - datetime.now()).days
        applications.append({
            "id": row[0],
            "subject": row[1],
            "department": row[2],
            "pio_name": row[3],
            "state": row[4],
            "filed_date": row[5],
            "deadline_date": row[6],
            "days_remaining": max(0, days_remaining),
            "status": row[7],
            "priority": calculate_priority(max(0, days_remaining), row[7]),
            "draft": row[8],
        })
    return applications


def update_application_status(application_id: int, user_name: str, status: str, user_key: str | None = None) -> dict:
    allowed_statuses = {"Pending", "Filed", "Response Received", "Appeal Needed", "Closed"}
    if status not in allowed_statuses:
        return {
            "success": False,
            "message": "Invalid status selected."
        }

    if use_supabase():
        try:
            return update_supabase_status(application_id, user_name, status, user_key)
        except Exception as error:
            print(f"Supabase status update failed, using SQLite fallback: {error}")

    lookup_key = normalize_lookup_key(user_key or user_name)
    init_tracker_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE rti_applications
        SET status = ?
        WHERE id = ? AND (user_key = ? OR (user_key IS NULL AND user_name = ?))
    """, (status, application_id, lookup_key, user_name))
    conn.commit()
    updated = cur.rowcount
    conn.close()

    return {
        "success": updated > 0,
        "application_id": application_id,
        "status": status,
        "message": "Status updated successfully." if updated else "Application not found."
    }


def get_dashboard_stats(user_name: str) -> dict:
    applications = get_all_applications(user_name)
    total = len(applications)
    pending = sum(1 for app in applications if app["status"] in {"Pending", "Filed"})
    closed = sum(1 for app in applications if app["status"] == "Closed")
    urgent = sum(1 for app in applications if app["priority"] == "High")

    departments = {}
    for app in applications:
        departments[app["department"]] = departments.get(app["department"], 0) + 1

    top_departments = [
        {"department": department, "count": count}
        for department, count in sorted(
            departments.items(),
            key=lambda item: item[1],
            reverse=True
        )[:5]
    ]

    return {
        "total_applications": total,
        "pending_cases": pending,
        "closed_cases": closed,
        "urgent_cases": urgent,
        "top_departments": top_departments,
        "recent_applications": applications[:5]
    }


def calculate_priority(days_remaining: int, status: str) -> str:
    if status in {"Closed", "Response Received"}:
        return "Low"
    if days_remaining <= 7:
        return "High"
    if days_remaining <= 15:
        return "Medium"
    return "Normal"


def normalize_lookup_key(value: str | None) -> str:
    return (value or "").strip().lower()


def run_supabase_tracker_agent(
    user_name: str,
    user_address: str,
    intent: dict,
    authority: dict,
    draft: str,
    user_key: str | None,
    filed_date: str,
    deadline_date: str,
    days_remaining: int,
) -> dict:
    payload = {
        "user_key": normalize_lookup_key(user_key or user_name),
        "user_name": user_name,
        "user_address": user_address,
        "subject": intent["subject"],
        "department": authority["department"],
        "pio_name": authority["pio_name"],
        "pio_address": authority["address"],
        "state": intent["state"],
        "draft": draft,
        "filed_date": filed_date,
        "deadline_date": deadline_date,
        "status": "Pending",
    }
    response = requests.post(
        supabase_endpoint(),
        headers=supabase_headers(prefer_return=True),
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    row = response.json()[0]

    return {
        "application_id": row["id"],
        "filed_date": filed_date,
        "deadline_date": deadline_date,
        "days_remaining": days_remaining,
        "status": "Pending",
        "storage": "Supabase",
        "message": f"RTI saved to Supabase! Government must respond by {deadline_date} (30 days)"
    }


def get_supabase_applications(user_name: str, lookup_key: str) -> list:
    response = requests.get(
        supabase_endpoint(),
        headers=supabase_headers(),
        params={
            "select": "id,subject,department,pio_name,state,filed_date,deadline_date,status,draft",
            "or": f"(user_key.eq.{lookup_key},and(user_key.is.null,user_name.eq.{user_name}))",
            "order": "filed_date.desc,id.desc",
        },
        timeout=20,
    )
    response.raise_for_status()

    applications = []
    for row in response.json():
        deadline = datetime.strptime(row["deadline_date"], "%Y-%m-%d")
        days_remaining = (deadline - datetime.now()).days
        status = row.get("status") or "Pending"
        applications.append({
            "id": row["id"],
            "subject": row["subject"],
            "department": row["department"],
            "pio_name": row["pio_name"],
            "state": row["state"],
            "filed_date": row["filed_date"],
            "deadline_date": row["deadline_date"],
            "days_remaining": max(0, days_remaining),
            "status": status,
            "priority": calculate_priority(max(0, days_remaining), status),
            "draft": row["draft"],
        })
    return applications


def update_supabase_status(application_id: int, user_name: str, status: str, user_key: str | None = None) -> dict:
    response = requests.patch(
        supabase_endpoint(),
        headers=supabase_headers(prefer_return=True),
        params={
            "id": f"eq.{application_id}",
            "or": f"(user_key.eq.{normalize_lookup_key(user_key or user_name)},and(user_key.is.null,user_name.eq.{user_name}))",
        },
        json={"status": status},
        timeout=20,
    )
    response.raise_for_status()
    rows = response.json()

    return {
        "success": bool(rows),
        "application_id": application_id,
        "status": status,
        "storage": "Supabase",
        "message": "Status updated successfully." if rows else "Application not found."
    }
