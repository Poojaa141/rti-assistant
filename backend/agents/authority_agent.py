import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "rti.db"

STOP_WORDS = {
    "about", "after", "also", "announcement", "been", "date", "declaration",
    "delay", "expected", "from", "have", "know", "months",
    "please", "status", "that", "their", "there", "this", "want", "what",
    "when", "where", "which", "with", "would", "your",
}

KEYWORD_ALIASES = {
    "exam": ["education", "school", "college", "university", "result"],
    "examination": ["education", "school", "college", "university", "result"],
    "semester": ["education", "college", "university", "result"],
    "results": ["result", "education", "college", "university"],
}


def run_authority_agent(intent: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    row, score, keyword_count = find_best_keyword_match(cur, intent)
    method = "keyword_match"

    if not row:
        cur.execute("""
            SELECT department, pio_name, address, fee, level, website, notes, category
            FROM departments WHERE department LIKE ?
        """, (f"%{intent['department']}%",))
        row = cur.fetchone()
        method = "department_name_match"

    if not row:
        cur.execute("""
            SELECT department, pio_name, address, fee, level, website, notes, category
            FROM departments WHERE keywords LIKE ?
        """, (f"%{intent['department'].lower()}%",))
        row = cur.fetchone()
        method = "keywords_column_match"

    conn.close()

    if row:
        confidence = compute_confidence(method, score, keyword_count)
        return {
            "department": row[0],
            "pio_name": row[1],
            "address": row[2],
            "fee": row[3],
            "level": row[4],
            "website": row[5],
            "notes": row[6],
            "confidence": f"{confidence}%",
            "category": row[7] or row[0],
        }

    confidence = compute_confidence("no_match")
    return {
        "department": intent["department"],
        "pio_name": "Public Information Officer",
        "address": "Concerned Government Office",
        "fee": 10,
        "level": "State",
        "website": "https://rtionline.gov.in",
        "notes": "File online at rtionline.gov.in",
        "confidence": f"{confidence}%",
        "category": "General Administration",
    }


def find_best_keyword_match(cur, intent: dict):
    """
    Returns (best_row, best_score, keyword_count). best_row is an 8-tuple
    matching the shape used elsewhere in this file:
    (department, pio_name, address, fee, level, website, notes, category).
    """
    keywords = extract_keywords(intent.get("subject", ""))
    if not keywords:
        return None, 0, 0

    cur.execute("""
        SELECT department, pio_name, address, fee, level, website, notes, keywords, category
        FROM departments
    """)

    best_row = None
    best_score = 0
    for row in cur.fetchall():
        department = row[0].lower()
        keyword_blob = (row[7] or "").lower()
        score = 0
        for keyword in keywords:
            if keyword in keyword_blob:
                score += 3
            if keyword in department:
                score += 2
        if score > best_score:
            best_score = score
            best_row = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[8])

    if best_score >= 3:
        return best_row, best_score, len(keywords)
    return None, 0, len(keywords)


def compute_confidence(method: str, score: int = 0, keyword_count: int = 0) -> int:
    """
    Converts the match method and keyword-score strength into a confidence
    percentage that can actually be explained and defended:

    - keyword_match: scaled by how much of the maximum possible score was
      hit. A complaint where every extracted keyword matched the
      department's keyword list strongly scores near 98%; a weak partial
      match (just barely over the qualifying threshold of 3) scores closer
      to 65%.
    - department_name_match / keywords_column_match: these fallback paths
      don't carry a graded score in the original logic (they're simple SQL
      LIKE lookups), so they get fixed, lower confidence bands reflecting
      that they're known to be less precise than the keyword-scored match.
    - no_match: nothing in the database matched at all, so a generic
      authority is returned and confidence is set low to signal the user
      should manually verify the department before filing.
    """
    if method == "keyword_match":
        if keyword_count == 0:
            return 70
        max_possible = keyword_count * 5  # 3 (keyword list hit) + 2 (department name hit) per keyword
        ratio = min(1.0, score / max_possible)
        confidence = 65 + ratio * 33
        return round(min(98, confidence))
    if method == "department_name_match":
        return 78
    if method == "keywords_column_match":
        return 62
    return 35  # no_match


def extract_keywords(text: str) -> list:
    words = re.findall(r"[a-zA-Z][a-zA-Z/-]+", text.lower())
    keywords = []
    for word in words:
        if len(word) <= 3 or word in STOP_WORDS:
            continue
        keywords.append(word)
        if word.endswith("s"):
            keywords.append(word[:-1])
        keywords.extend(KEYWORD_ALIASES.get(word, []))
    return list(dict.fromkeys(keywords))


if __name__ == "__main__":
    test_intent = {"subject": "ration card rejection reason", "department": "Public Distribution System"}
    print(run_authority_agent(test_intent))
