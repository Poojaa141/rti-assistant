"""
One-time migration: adds a `category` column to the departments table and
backfills it by matching each department's name and keywords against a
curated set of category patterns.

Safe to re-run -- it only adds the column once (checked via PRAGMA
table_info), but always re-applies categorization on every run. That means
you can tweak CATEGORY_RULES below and re-run this as many times as you
want while you're refining the mapping.

Place this file in your `backend/` folder (next to main.py and rti.db) and
run it once with: python migrate_add_category.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "rti.db"

# Ordered: more specific patterns are listed first so a department that
# could match multiple rules gets the most relevant category rather than
# whichever generic one happens to come first alphabetically.
CATEGORY_RULES = [
    ("Identity & Documentation", [
        "passport", "aadhaar", "aadhar", "voter", "election",
        "birth certificate", "death certificate",
    ]),
    ("Public Distribution & Food Security", [
        "ration", "pds", "public distribution", "food", "fci", "civil supplies",
    ]),
    ("Public Utilities", [
        "electricity", "power", "water supply", "water board", "gas", "lpg",
    ]),
    ("Transport", [
        "railway", "railways", "rto", "transport", "roadways", "metro",
    ]),
    ("Welfare & Social Security", [
        "pension", "epfo", "provident fund", "social welfare",
        "disability", "widow", "old age",
    ]),
    ("Law & Order", [
        "police", "court", "judiciary", "prison", "jail", "magistrate",
    ]),
    ("Education", [
        "education", "scholarship", "school", "university", "college", "ugc",
    ]),
    ("Health", [
        "health", "hospital", "medical", "pharmacy", "ayush",
    ]),
    ("Revenue & Land Records", [
        "land record", "registration", "revenue", "survey",
        "property tax", "stamp duty",
    ]),
    ("Banking & Finance", [
        "bank", "income tax", "gst", "rbi", "finance",
    ]),
    ("Employment & Labour", [
        "labour", "labor", "employment", "mgnrega", "wages",
    ]),
    ("Civic & Municipal Services", [
        "municipal", "corporation", "panchayat", "building permission",
        "sanitation", "ghmc",
    ]),
]

DEFAULT_CATEGORY = "General Administration"


def categorize(department: str, keywords: str) -> str:
    text = f"{department or ''} {keywords or ''}".lower()
    for category, patterns in CATEGORY_RULES:
        if any(pattern in text for pattern in patterns):
            return category
    return DEFAULT_CATEGORY


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(departments)")
    existing_columns = [row[1] for row in cur.fetchall()]
    if "category" not in existing_columns:
        cur.execute("ALTER TABLE departments ADD COLUMN category TEXT")
        print("Added 'category' column.")
    else:
        print("'category' column already exists -- re-applying categorization.")

    cur.execute("SELECT rowid, department, keywords FROM departments")
    rows = cur.fetchall()

    unmatched = []
    for rowid, department, keywords in rows:
        category = categorize(department, keywords)
        if category == DEFAULT_CATEGORY:
            unmatched.append(department)
        cur.execute("UPDATE departments SET category = ? WHERE rowid = ?", (category, rowid))

    conn.commit()
    conn.close()

    print(f"Categorized {len(rows)} department rows.")
    if unmatched:
        print("\nThese fell back to 'General Administration' -- consider adding a dedicated rule for them:")
        for name in unmatched:
            print(f"  - {name}")


if __name__ == "__main__":
    migrate()