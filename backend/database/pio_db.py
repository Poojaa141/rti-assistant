import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"

CATEGORY_RULES = [
    ("Identity & Documentation", [
        "passport", "aadhaar", "aadhar", "voter", "election",
        "birth certificate", "death certificate",
    ]),
    ("Public Distribution & Food Security", [
        "ration", "pds", "public distribution", "food", "civil supplies",
    ]),
    ("Public Utilities", [
        "electricity", "power", "water supply", "water board", "gas", "lpg",
    ]),
    ("Transport", [
        "railway", "railways", "train", "ticket", "refund", "rto", "transport", "metro",
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
        "sanitation", "garbage", "drainage",
    ]),
]

DEFAULT_CATEGORY = "General Administration"

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
            level TEXT,
            state TEXT DEFAULT 'All',
            keywords TEXT,
            website TEXT,
            notes TEXT,
            category TEXT
        )
    """)
    ensure_category_column(cur)
    remove_duplicate_departments(cur)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS departments_department_unique_idx
        ON departments (department)
    """)
    data = [
        ("Food and Civil Supplies", "Public Information Officer",
         "State Food & Civil Supplies Dept HQ", 10, "State", "All",
         "ration card,food grain,fair price shop,ration,PDS,BPL card,APL card,food subsidy",
         "https://dfpd.gov.in", "Apply with Rs.10 fee by postal order"),

        ("Public Distribution System", "PIO, PDS Office",
         "State Civil Supplies HQ", 10, "State", "All",
         "PDS,public distribution,ration shop,kerosene,wheat,rice,sugar,fair price",
         "https://dfpd.gov.in", "State level PDS authority"),

        ("Ministry of External Affairs", "CPIO, Ministry of External Affairs",
         "Patiala House, Tilak Marg, New Delhi - 110001", 10, "Central", "All",
         "passport,PSK,passport seva,police verification,visa,travel document,passport delay,passport pending",
         "https://www.passportindia.gov.in", "For passport related RTIs send to MEA"),

        ("Police Department", "PIO, State Police HQ",
         "State Police Headquarters", 10, "State", "All",
         "police,FIR,complaint,crime,theft,assault,harassment,police station,constable,officer,arrest",
         "https://police.gov.in", "File at concerned state police HQ"),

        ("Municipal Corporation", "PIO, Municipal Office",
         "City Municipal Corporation Office", 10, "State", "All",
         "municipal,corporation,property tax,building permit,garbage,drainage,sewage,street light,birth certificate,death certificate",
         "https://mohua.gov.in", "File at local municipal corporation office"),

        ("Income Tax Department", "CPIO, Income Tax Dept",
         "CBDT, North Block, New Delhi - 110001", 10, "Central", "All",
         "income tax,IT,PAN card,PAN,tax refund,tax return,ITR,TDS,tax notice,assessment",
         "https://incometaxindia.gov.in", "For PAN related queries contact NSDL"),

        ("Indian Railways", "CPIO, Railway Board",
         "Rail Bhavan, Raisina Road, New Delhi - 110001", 10, "Central", "All",
         "railway,train,ticket,reservation,refund,railway station,rail,IRCTC,coach,berth,platform",
         "https://indianrailways.gov.in", "Zone wise RTI also applicable"),

        ("Education Department", "PIO, Education Dept",
         "State Education Department HQ", 10, "State", "All",
         "school,college,university,education,scholarship,admission,result,marksheet,degree,certificate,teacher,principal",
         "https://education.gov.in", "For central universities contact UGC"),

        ("Health Department", "PIO, Health Dept",
         "State Health Department HQ", 10, "State", "All",
         "hospital,health,medical,doctor,nurse,medicine,ambulance,treatment,PHC,dispensary",
         "https://mohfw.gov.in", "For central hospitals contact MoHFW"),

        ("Water Supply Department", "PIO, Water Supply Board",
         "State Water Supply & Sanitation Board", 10, "State", "All",
         "water,water supply,water bill,pipeline,water connection,borewell,tap water,water tank,water meter",
         "https://jalshakti-ddws.gov.in", "State water boards handle local complaints"),

        ("Transport Department", "PIO, Transport Dept",
         "State Transport Authority", 10, "State", "All",
         "driving licence,driving license,vehicle,registration,RC book,RTO,transport,bus,auto,taxi,fitness certificate",
         "https://parivahan.gov.in", "Contact RTO for vehicle related RTIs"),

        ("Land Records Department", "PIO, Revenue Dept",
         "State Revenue Department HQ", 10, "State", "All",
         "land,property,mutation,registry,land record,patta,khata,survey,boundary,encroachment,revenue",
         "https://dolr.gov.in", "Contact tehsildar or district collector"),

        ("Electricity Board", "PIO, State Electricity Board",
         "State Electricity Distribution Company HQ", 10, "State", "All",
         "electricity,power,current,bill,meter,connection,transformer,load shedding,power cut,electric,voltage",
         "https://mnre.gov.in", "Contact state DISCOM for electricity RTIs"),

        ("Public Works Department", "PIO, PWD Office",
         "State Public Works Department HQ", 10, "State", "All",
         "road,pothole,bridge,construction,building,highway,repair,footpath,drain,culvert,PWD,infrastructure",
         "https://morth.nic.in", "For national highways contact NHAI"),

        ("Social Welfare Department", "PIO, Social Welfare Dept",
         "State Social Welfare Department HQ", 10, "State", "All",
         "pension,widow pension,disability,handicap,old age,senior citizen,welfare,SC,ST,OBC,caste certificate",
         "https://socialjustice.gov.in", "Contact district social welfare office"),

        ("Pension Department", "PIO, Pension Dept",
         "State Pension Directorate", 10, "State", "All",
         "pension,retirement,gratuity,provident fund,PF,EPF,superannuation,family pension,pension delay",
         "https://epfindia.gov.in", "For EPFO contact regional PF office"),

        ("UIDAI", "CPIO, UIDAI",
         "UIDAI HQ, Bangla Sahib Road, New Delhi - 110001", 10, "Central", "All",
         "aadhaar,aadhar,UID,biometric,fingerprint,iris,aadhaar update,aadhaar correction,aadhaar card,enrollment",
         "https://uidai.gov.in", "Aadhaar issues handled centrally by UIDAI"),

        ("Election Commission", "PIO, State Election Office",
         "Chief Electoral Officer, State Election Commission", 10, "State", "All",
         "voter ID,voter card,election,EPIC,electoral roll,polling booth,vote,voter list,voter registration",
         "https://eci.gov.in", "For voter ID issues contact CEO of state"),

        ("University Grants Commission", "CPIO, UGC",
         "Bahadur Shah Zafar Marg, New Delhi - 110002", 10, "Central", "All",
         "university,UGC,college,degree,recognition,affiliation,higher education,PhD,scholarship,fellowship",
         "https://ugc.ac.in", "For state universities contact state education dept"),

        ("Gram Panchayat", "PIO, Gram Panchayat",
         "Concerned Gram Panchayat Office", 10, "State", "All",
         "panchayat,village,gram,MNREGA,NREGA,job card,rural,sarpanch,ward,pradhan,gram sabha",
         "https://egramswaraj.gov.in", "File at local panchayat or block office"),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO departments
        (department, pio_name, address, fee, level, state, keywords, website, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, data)
    update_department_categories(cur)
    conn.commit()
    conn.close()
    print(f"Database created successfully with {len(data)} departments!")


def ensure_category_column(cur):
    cur.execute("PRAGMA table_info(departments)")
    columns = {row[1] for row in cur.fetchall()}
    if "category" not in columns:
        cur.execute("ALTER TABLE departments ADD COLUMN category TEXT")


def update_department_categories(cur):
    cur.execute("SELECT id, department, keywords FROM departments")
    for department_id, department, keywords in cur.fetchall():
        cur.execute(
            "UPDATE departments SET category = ? WHERE id = ?",
            (categorize_department(department, keywords), department_id),
        )


def categorize_department(department: str, keywords: str) -> str:
    text = f"{department or ''} {keywords or ''}".lower()
    for category, patterns in CATEGORY_RULES:
        if any(pattern in text for pattern in patterns):
            return category
    return DEFAULT_CATEGORY


def remove_duplicate_departments(cur):
    cur.execute("""
        DELETE FROM departments
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM departments
            GROUP BY department
        )
    """)

if __name__ == "__main__":
    create_db()
