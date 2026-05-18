import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            department TEXT,
            pio_name TEXT,
            address TEXT,
            fee INTEGER,
            level TEXT
        )
    """)
    data = [
        ("Food and Civil Supplies", "Public Information Officer", "State Food Dept HQ", 10, "State"),
        ("Public Distribution System", "PIO, PDS Office", "State Civil Supplies HQ", 10, "State"),
        ("Income Tax", "CPIO, Income Tax Dept", "CBDT, North Block, New Delhi", 10, "Central"),
        ("Police", "PIO, State Police HQ", "State Police Headquarters", 10, "State"),
        ("Railways", "CPIO, Railway Board", "Rail Bhavan, New Delhi", 10, "Central"),
        ("Municipal Corporation", "PIO, Municipal Office", "City Municipal Corporation", 10, "State"),
        ("Passport", "CPIO, Ministry of External Affairs", "Patiala House, New Delhi", 10, "Central"),
        ("Land Records", "PIO, Revenue Dept", "State Revenue Department", 10, "State"),
        ("Education", "PIO, Education Dept", "State Education HQ", 10, "State"),
        ("Health", "PIO, Health Dept", "State Health Department HQ", 10, "State"),
        ("Water Supply", "PIO, Water Dept", "State Water Supply Board", 10, "State"),
        ("Transport", "PIO, Transport Dept", "State Transport Authority", 10, "State"),
        ("Election Commission", "PIO, Election Office", "State Election Commission HQ", 10, "State"),
        ("Revenue", "PIO, Revenue Dept", "State Revenue Department", 10, "State"),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO departments 
        (department, pio_name, address, fee, level) 
        VALUES (?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    create_db()
