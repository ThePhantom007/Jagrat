"""Budgeted live Gemini check. Use a SEPARATE test API key/project so your demo quota is untouched.

    python scripts/live_gemini_check.py sdk       # 1 call, fast model: verifies key, model name, SDK call shape
    python scripts/live_gemini_check.py mentor    # ~2-3 calls: full /api/mentor flow + authenticity checks
    python scripts/live_gemini_check.py vs        # ~2-3 calls: Vivekananda-vs-Me flow

Every Gemini call is counted and capped (MAX_CALLS, default 4; override with env var). Uses a throwaway database.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

mode = sys.argv[1] if len(sys.argv) > 1 else "sdk"
MAX_CALLS = int(os.environ.get("MAX_CALLS", "4"))
_tmp = tempfile.mkdtemp(prefix="jagrat-live-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/live.db"
os.environ["SEED_DEMO_ON_STARTUP"] = "false"

from app.config import get_settings  # noqa: E402

if not get_settings().gemini_api_key:
    sys.exit("GEMINI_API_KEY is not set (put your TEST key in .env or the environment).")

from app.services import gemini as gemini_module  # noqa: E402

calls = {"n": 0}
_original = gemini_module.GeminiService.generate


def counted(self, **kwargs):
    if calls["n"] >= MAX_CALLS:
        raise gemini_module.GeminiUnavailableError(f"call cap ({MAX_CALLS}) reached; stopping to protect quota")
    calls["n"] += 1
    print(f"  -> Gemini call #{calls['n']} ({'fast' if kwargs.get('fast') else 'main'} model, prompt {len(kwargs.get('prompt', ''))} chars)")
    return _original(self, **kwargs)


gemini_module.GeminiService.generate = counted

if mode == "sdk":
    from app.schemas import RiskResult

    svc = gemini_module.GeminiService()
    out = svc.generate(system_instruction="Classify risk. Return JSON only.", prompt="I am nervous about my exam tomorrow.", schema=RiskResult, fast=True)
    print("OK, structured output parsed:", out)
    print(f"Gemini calls used: {calls['n']}")
    sys.exit(0)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ONBOARDING = {
    "profession": "student", "age": 20, "matters_most": "studies", "troubling_most": "confidence",
    "problem_approach": "overthink", "improve": "confidence",
}
with TestClient(app) as client:
    token = client.post("/api/profile", json={"display_name": "Live"}).json()["access_token"]
    h = {"X-Profile-Token": token}
    client.put("/api/profile/onboarding", headers=h, json=ONBOARDING)

    if mode == "mentor":
        r = client.post("/api/mentor", headers=h, json={"message": "I failed my examination and feel that I am not capable."})
    elif mode == "vs":
        r = client.post("/api/vivekananda-vs-me", headers=h, json={"view": "I think failure shows who is capable and who is not."})
    else:
        sys.exit("mode must be sdk, mentor or vs")

    print("HTTP status:", r.status_code)
    data = r.json()
    if r.status_code != 200:
        print(data)
        print(f"Gemini calls used: {calls['n']}")
        sys.exit(1)

    teaching = data.get("teaching")
    if teaching:
        from app.db.session import SessionLocal
        from app.models import Teaching

        with SessionLocal() as db:
            stored = db.get(Teaching, teaching["id"])
        print("teaching id:", teaching["id"], "| words:", teaching.get("word_count"), "| title:", teaching["source"]["title"])
        print("quote is byte-identical to stored canonical text:", stored is not None and stored.quote == teaching["quote"])
        print("trust.quote_verified:", data["trust"]["quote_verified"])
    else:
        print("No teaching selected; trust note:", data["trust"].get("source_note"))

    ai_fields = [v for k, v in data.items() if isinstance(v, str) and k not in ("status", "conversation_id", "my_view")]
    from app.services.mentor import validate_ai_written_text
    try:
        validate_ai_written_text(*ai_fields)
        print("AI-written text passes the source guard: True")
    except Exception as exc:  # noqa: BLE001
        print("AI-written text passes the source guard: False ->", exc)

    print("\nSample AI text:", (data.get("interpretation") or data.get("where_they_align") or "")[:300])
    print(f"\nGemini calls used: {calls['n']}")
