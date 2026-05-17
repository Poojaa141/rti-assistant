import sqlite3

def run_authority_agent(intent: dict) -> dict:
    conn = sqlite3.connect("rti.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT department, pio_name, address, fee, level 
        FROM departments 
        WHERE department LIKE ?
    """, (f"%{intent['department']}%",))

    row = cur.fetchone()
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