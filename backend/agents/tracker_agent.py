import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"


def init_tracker_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rti_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.commit()
    conn.close()


def run_tracker_agent(user_name: str, user_address: str, intent: dict, authority: dict, draft: str) -> dict:
    init_tracker_db()

    today = datetime.now()
    filed_date = today.strftime("%Y-%m-%d")
    deadline_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    days_remaining = 30

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rti_applications
        (user_name, user_address, subject, department, pio_name, pio_address, state, draft, filed_date, deadline_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
        "Pending",
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
        "message": f"RTI saved! Government must respond by {deadline_date} (30 days)",
    }


def get_all_applications(user_name: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, subject, department, filed_date, deadline_date, status
        FROM rti_applications
        WHERE user_name = ?
        ORDER BY filed_date DESC
    """, (user_name,))
    rows = cur.fetchall()
    conn.close()

    applications = []
    for row in rows:
        deadline = datetime.strptime(row[4], "%Y-%m-%d")
        days_remaining = (deadline - datetime.now()).days

        applications.append({
            "id": row[0],
            "subject": row[1],
            "department": row[2],
            "filed_date": row[3],
            "deadline_date": row[4],
            "days_remaining": max(0, days_remaining),
            "status": row[5],
        })
    return applications


if __name__ == "__main__":
    intent = {
        "subject": "ration card rejection reason",
        "department": "Public Distribution System (PDS)",
        "state": "Maharashtra",
    }
    authority = {
        "department": "Public Distribution System (PDS)",
        "pio_name": "Public Information Officer",
        "address": "State Civil Supplies HQ, Maharashtra",
        "fee": 10,
        "level": "State",
    }
    draft = "Sample RTI letter content here"

    print("Agent 4 saving RTI application...")
    result = run_tracker_agent("Pooja Patil", "Pune, Maharashtra", intent, authority, draft)
    print("Saved!", result)

    print("\nAll your RTI applications:")
    apps = get_all_applications("Pooja Patil")
    for app in apps:
        print(f"-> ID:{app['id']} | {app['subject']} | Deadline: {app['deadline_date']} | {app['days_remaining']} days left | {app['status']}")
