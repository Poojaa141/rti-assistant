import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"

def run_authority_agent(intent: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Search 1 — match department name
    cur.execute("""
        SELECT department, pio_name, address, fee, level, website, notes
        FROM departments WHERE department LIKE ?
    """, (f"%{intent['department']}%",))
    row = cur.fetchone()

    # Search 2 — match keywords using department name
    if not row:
        cur.execute("""
            SELECT department, pio_name, address, fee, level, website, notes
            FROM departments WHERE keywords LIKE ?
        """, (f"%{intent['department'].lower()}%",))
        row = cur.fetchone()

    # Search 3 — match keywords using subject words
    if not row:
        subject_words = intent.get("subject", "").lower().split()
        for word in subject_words:
            if len(word) > 3:
                cur.execute("""
                    SELECT department, pio_name, address, fee, level, website, notes
                    FROM departments WHERE keywords LIKE ?
                """, (f"%{word}%",))
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
            "level":      row[4],
            "website":    row[5],
            "notes":      row[6],
        }
    else:
        return {
            "department": intent["department"],
            "pio_name":   "Public Information Officer",
            "address":    "Concerned Government Office",
            "fee":        10,
            "level":      "State",
            "website":    "https://rtionline.gov.in",
            "notes":      "File online at rtionline.gov.in",
        }