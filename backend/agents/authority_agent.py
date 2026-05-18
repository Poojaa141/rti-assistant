import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"

def run_authority_agent(intent: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    department = intent["department"]
    search_terms = [
        department,
        department.replace("(PDS)", "").strip(),
        department.replace("Department", "").strip(),
    ]

    row = None
    for term in search_terms:
        if not term:
            continue
        cur.execute("""
            SELECT department, pio_name, address, fee, level
            FROM departments
            WHERE department LIKE ?
        """, (f"%{term}%",))
        row = cur.fetchone()
        if row:
            break

    conn.close()

    if row:
        return {
            "department": row[0],
            "pio_name":   row[1],
            "address":    row[2],
            "fee":        row[3],
            "level":      row[4]
        }
    else:
        return {
            "department": intent["department"],
            "pio_name":   "Public Information Officer",
            "address":    "Concerned Government Office",
            "fee":        10,
            "level":      "State"
        }
