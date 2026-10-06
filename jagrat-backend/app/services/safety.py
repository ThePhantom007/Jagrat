from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import RiskResult


# Deliberately high-signal patterns. We avoid bare "die/death" and "going to die"
# because ordinary figurative language such as "die of embarrassment" is common.
IMMEDIATE_PATTERNS = [
    re.compile(r"\bkill myself\b", re.I),
    re.compile(r"\bend my life\b", re.I),
    re.compile(r"\bend it all\b", re.I),
    re.compile(r"\bi (?:don't|do not|dont) want to live(?: anymore| any more)?\b", re.I),
    re.compile(r"\bi (?:can't|cannot|cant) (?:go on|keep going)\b", re.I),
    re.compile(r"\b(?:wish|i wish) (?:i were|i was) dead\b", re.I),
    re.compile(r"\bbetter off dead\b", re.I),
    re.compile(r"\bno reason to live\b", re.I),
    re.compile(r"\b(?:suicide|suicidal)\b", re.I),
    re.compile(r"\bhurt myself\b", re.I),
    re.compile(r"\bself[- ]harm\b", re.I),
    re.compile(r"\bcut myself\b", re.I),
    re.compile(r"\b(?:kill|murder|hurt|attack) (?:him|her|them|someone)\b", re.I),
    # High-signal Hindi/Hinglish forms.
    re.compile(r"\b(?:marna|marne|mar\s+ja(?:na|unga|ungi)|mar\s+jana)\s+(?:chahta|chahti)(?:\s+hoon)?\b", re.I),
    re.compile(r"\b(?:mujhe|main)\s+(?:marna|mar\s+jana)\s+(?:hai|chahta|chahti)(?:\s+hoon)?\b", re.I),
    re.compile(r"\b(?:jeena|jeene)\s+nahi\s+(?:chahta|chahti)(?:\s+hoon)?\b", re.I),
    re.compile(r"\b(?:mujhe|main)\s+(?:jeena|jeene)\s+nahi\s+(?:hai|chahta|chahti)(?:\s+hoon)?\b", re.I),
    re.compile(r"\bmujhe\s+nahi\s+jeena(?:\s+hai)?\b", re.I),
    re.compile(r"\b(?:ab\s+aur\s+nahi\s+jeena|ab\s+nahi\s+jeena)\b", re.I),
    re.compile(r"\b(?:zindagi|jindagi)\s+(?:khatam|khtm)\s+(?:karna|kar\s+du(?:n)?|kar\s+doon)\b", re.I),
    re.compile(r"\bkhud\s+ko\s+khatam\s+(?:karna|kar\s+du(?:n)?|kar\s+doon)\b", re.I),
    re.compile(r"\bapni\s+jaan\s+(?:lena|de(?:\s+doon|\s+du(?:n)?|\s+dungi|\s+dunga)?)\b", re.I),
    re.compile(r"\b(?:sab\s+khatam|sabkuch\s+khatam)\s+(?:kar(?:na|doon|du)|ho\s+jaye)\b", re.I),
    re.compile(r"\bkhudkhushi\b", re.I),
]


@dataclass(frozen=True)
class _PhraseRule:
    pattern: re.Pattern[str]
    reason: str


COMPILED_RULES = [_PhraseRule(pattern=p, reason="High-signal acute safety language detected locally.") for p in IMMEDIATE_PATTERNS]


def local_risk_check(text: str) -> RiskResult | None:
    normalized = re.sub(r"\s+", " ", text.casefold()).strip()
    for rule in COMPILED_RULES:
        if rule.pattern.search(normalized):
            return RiskResult(risk_level="immediate", reason=rule.reason)
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
