import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def run_draft_agent(intent: dict, authority: dict, user_name: str = "Pooja Patil", user_address: str = "Pune, Maharashtra") -> str:
    today = datetime.now().strftime("%d %B %Y")

    prompt = f"""
You are an RTI filing expert in India. Write a formal RTI application based on the details below.

Applicant Name: {user_name}
Applicant Address: {user_address}
Subject: {intent['subject']}
Department: {authority['department']}
PIO Name: {authority['pio_name']}
PIO Address: {authority['address']}
RTI Fee: Rs. {authority['fee']}
State: {intent['state']}
Date: {today}

Write a complete formal RTI application letter following the exact format below:

To,
The Public Information Officer,
[Department Name],
[Address]

Subject: Application under Right to Information Act, 2005

Respected Sir/Madam,

I, [Applicant Name], residing at [Applicant Address], hereby request the following information under Section 6(1) of the Right to Information Act, 2005:

1. [Write 3-4 specific questions related to the subject]

I am enclosing a fee of Rs.10/- as application fee.

If the information requested is held by another public authority, please transfer this application as per Section 6(3) of the RTI Act.

Yours faithfully,
[Applicant Name]
[Applicant Address]
Date: {today}

IMPORTANT:
- Keep the full application concise and under 500 words.
- Write only 3-4 focused information questions.
- Ask only for existing records, reasons, status, officer details, timelines, rules, copies of documents, and file notes.
- Do not ask for advice, suggestions, opinions, explanations of what the applicant should do, or future promises.
- Do not add a long background story.
- Fill in all details properly and use exactly this date: {today}.
"""

    try:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing from .env")

        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as error:
        print(f"Groq draft generation failed: {_friendly_error(error)}")
        print("Using local fallback RTI draft instead.")
        return fallback_draft(intent, authority, user_name, user_address, today)


def fallback_draft(intent: dict, authority: dict, user_name: str, user_address: str, today: str) -> str:
    fee = authority.get("fee", 10)
    return f"""To,
The Public Information Officer,
{authority['department']},
{authority['address']}

Subject: Application under Right to Information Act, 2005

Respected Sir/Madam,

I, {user_name}, residing at {user_address}, hereby request the following information under Section 6(1) of the Right to Information Act, 2005:

1. Please provide the reason for: {intent['subject']}.
2. Please provide copies of the records, notes, orders, or file remarks related to this matter.
3. Please provide the current status of my application/request and the name/designation of the officer handling it.
4. Please provide the prescribed rules, guidelines, or timeline applicable to processing this matter.

I am enclosing a fee of Rs.{fee}/- as application fee.

If the information requested is held by another public authority, please transfer this application as per Section 6(3) of the RTI Act.

Yours faithfully,
{user_name}
{user_address}
Date: {today}"""


def _friendly_error(error: Exception) -> str:
    message = str(error)
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if error.response is not None else "unknown"
        if status_code == 401:
            return "Groq API key is invalid or expired"
        if status_code == 429:
            return "Groq free-tier rate limit reached"
        return f"Groq API returned HTTP {status_code}"
    if "ProxyError" in error.__class__.__name__ or "proxy" in message.lower():
        return "could not connect to Groq through the current proxy"
    if "ConnectError" in error.__class__.__name__ or "connection" in message.lower():
        return "could not connect to Groq"
    return message.splitlines()[0]


if __name__ == "__main__":
    # Test data
    intent = {
        "subject": "ration card rejection reason",
        "department": "Public Distribution System (PDS)",
        "state": "Maharashtra"
    }
    authority = {
        "department": "Public Distribution System (PDS)",
        "pio_name": "Public Information Officer",
        "address": "State Civil Supplies HQ, Maharashtra",
        "fee": 10,
        "level": "State"
    }

    print("Agent 3 writing RTI application...\n")
    draft = run_draft_agent(intent, authority)
    print(draft)
