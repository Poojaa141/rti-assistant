import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

INTENT_PROMPT = """
You are an RTI filing assistant for India.
Extract information from the user query below.

Return ONLY this JSON format, nothing else:
{{
  "subject": "what information the person wants",
  "department": "which government department",
  "state": "which Indian state or Central"
}}

User query: {query}
"""

def run_intent_agent(query: str) -> dict:
    try:
        result = call_groq_intent_model(query)
        return json.loads(_clean_json_response(result))
    except Exception as error:
        print(f"Groq intent extraction failed: {_friendly_error(error)}")
        print("Using local fallback intent extraction instead.")
        return fallback_intent_extraction(query)


def call_groq_intent_model(query: str) -> str:
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
            "messages": [
                {
                    "role": "user",
                    "content": INTENT_PROMPT.format(query=query),
                }
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def fallback_intent_extraction(query: str) -> dict:
    query_lower = query.lower()
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh",
        "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu",
        "Lakshadweep",
    ]
    department_keywords = {
        "ration card": "Food and Civil Supplies Department",
        "passport": "Ministry of External Affairs",
        "income tax": "Income Tax Department",
        "pan card": "Income Tax Department",
        "aadhaar": "Unique Identification Authority of India",
        "driving licence": "Transport Department",
        "driving license": "Transport Department",
        "voter id": "Election Commission",
        "land record": "Revenue Department",
        "property": "Revenue Department",
        "police": "Police Department",
        "pension": "Social Welfare Department",
    }

    state = next((state for state in states if state.lower() in query_lower), "Central")
    department = next(
        (
            department
            for keyword, department in department_keywords.items()
            if keyword in query_lower
        ),
        "Concerned Public Information Officer",
    )

    return {
        "subject": query,
        "department": department,
        "state": state,
    }


def _clean_json_response(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    return cleaned


def _friendly_error(error: Exception) -> str:
    message = str(error)
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if error.response is not None else "unknown"
        if status_code == 401:
            return "Groq API key is invalid or expired"
        if status_code == 429:
            return "Groq free-tier rate limit reached"
        return f"Groq API returned HTTP {status_code}"
    if "ConnectError" in error.__class__.__name__ or "connection" in message.lower():
        return "could not connect to Groq"
    if isinstance(error, json.JSONDecodeError):
        return "Groq returned text that was not valid JSON"
    return message.splitlines()[0]


if __name__ == "__main__":
    test = run_intent_agent(
        "I want to know why my ration card was rejected in Maharashtra"
    )
    print(test)
