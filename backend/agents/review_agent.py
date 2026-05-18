import re


MAX_RTI_WORDS = 500


def run_review_agent(draft: str) -> dict:
    word_count = count_words(draft)
    checks = {
        "within_500_words": word_count <= MAX_RTI_WORDS,
        "mentions_rti_act": "Right to Information Act" in draft or "RTI Act" in draft,
        "has_subject": "Subject:" in draft,
        "has_date": "Date:" in draft,
        "has_questions": bool(re.search(r"(?m)^\s*1\.", draft)),
        "has_fee": "Rs." in draft or "fee" in draft.lower(),
        "has_transfer_clause": "Section 6(3)" in draft,
    }
    missing = [name for name, passed in checks.items() if not passed]

    return {
        "word_count": word_count,
        "max_words": MAX_RTI_WORDS,
        "passed": not missing,
        "checks": checks,
        "missing": missing,
        "message": "Draft is ready for review." if not missing else "Draft needs fixes before final use.",
    }


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w/-]+\b", text))


if __name__ == "__main__":
    sample = """Subject: Application under Right to Information Act, 2005

Respected Sir/Madam,

1. Please provide the requested information.

I am enclosing a fee of Rs.10/-.
If held elsewhere, transfer under Section 6(3).

Date: 18 May 2026"""
    print(run_review_agent(sample))
