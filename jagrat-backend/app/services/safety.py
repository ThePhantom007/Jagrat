from __future__ import annotations

import re

from app.schemas import RiskResult

IMMEDIATE_PATTERNS = [
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bsuicid(?:e|al)\b",
    r"\bwant to die\b",
    r"\bgoing to die\b",
    r"\bhurt myself\b",
    r"\bself[- ]harm\b",
    r"\bcut myself\b",
    r"\bkill (?:him|her|them|someone)\b",
    r"\bhurt (?:him|her|them|someone)\b",
    r"\battack (?:him|her|them|someone)\b",
]


def local_risk_check(text: str) -> RiskResult | None:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    for pattern in IMMEDIATE_PATTERNS:
        if re.search(pattern, normalized):
            return RiskResult(risk_level="immediate", reason="High-signal acute safety language detected locally.")
    return None


def safety_message() -> dict:
    return {
        "status": "safety",
        "message": (
            "I'm glad you shared this. Let's pause the reflection exercise and focus on getting human support. "
            "Please contact someone you trust and a professional support service. If you may be in immediate danger, "
            "contact emergency services now."
        ),
        "helplines": [
            {"name": "Tele-MANAS", "number": "14416", "description": "Government of India tele-mental health support"},
            {"name": "Tele-MANAS toll-free", "number": "1800-89-14416", "description": "Government of India tele-mental health support"},
            {"name": "Emergency Response Support System", "number": "112", "description": "India's pan-India emergency number"},
        ],
        "challenge_available": False,
    }
