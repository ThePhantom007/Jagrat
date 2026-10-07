"""Zero-token HTTP smoke test.

Runs the real FastAPI app in-process (no server needed) against a throwaway SQLite database with the Gemini key
forced empty, so NO Gemini request can be made. It checks routing, auth, onboarding, the local safety screen,
and the graceful 503 when Gemini is unavailable.

    python scripts/smoke_http.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

_tmp = tempfile.mkdtemp(prefix="jagrat-smoke-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/smoke.db"
os.environ["GEMINI_API_KEY"] = ""          # guarantees zero tokens are spent
os.environ["ENVIRONMENT"] = "development"
os.environ["DEMO_MODE"] = "false"
os.environ["SEED_DEMO_ON_STARTUP"] = "false"
os.environ["ALLOW_LEGACY_PROFILE_ID"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ONBOARDING = {
    "profession": "student", "age": 20, "matters_most": "studies", "troubling_most": "confidence",
    "problem_approach": "overthink", "improve": "confidence",
}
results: list[tuple[bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((condition, name))
    print(("PASS  " if condition else "FAIL  ") + name + (f"   [{detail}]" if detail and not condition else ""))


with TestClient(app) as client:  # entering the context runs startup (imports the teaching JSON)
    r = client.get("/health")
    check("GET /health -> 200 ok", r.status_code == 200 and r.json().get("status") == "ok", r.text)

    r = client.get("/api/profile")
    check("GET /api/profile without token -> 401", r.status_code == 401, str(r.status_code))

    r = client.post("/api/profile", json={"display_name": "Smoke"})
    check("POST /api/profile -> 201 with access_token", r.status_code == 201 and "access_token" in r.json(), r.text)
    token = r.json().get("access_token", "")
    auth = {"X-Profile-Token": token}

    r = client.get("/api/profile", headers=auth)
    check("GET /api/profile with token -> 200", r.status_code == 200, r.text)

    r = client.post("/api/mentor", headers=auth, json={"message": "I failed my exam and feel I am not capable."})
    check("mentor before onboarding -> 409", r.status_code == 409, f"{r.status_code} {r.text[:120]}")

    r = client.put("/api/profile/onboarding", headers=auth, json=ONBOARDING)
    check("PUT /api/profile/onboarding -> 200", r.status_code == 200, r.text)

    r = client.put("/api/profile/onboarding", headers=auth, json={**ONBOARDING, "profession": "wizard"})
    check("invalid onboarding value -> 422", r.status_code == 422, str(r.status_code))

    r = client.get("/api/teachings", headers=auth, params={"query": "fear"})
    body = r.json() if r.status_code == 200 else []
    check("GET /api/teachings?query=fear -> non-empty list", r.status_code == 200 and len(body) > 0, r.text[:120])

    for phrase in ("I want to die", "I want to kill myself", "mujhe marna hai"):
        r = client.post("/api/mentor", headers=auth, json={"message": phrase})
        check(f"mentor crisis phrase '{phrase}' -> safety response", r.status_code == 200 and r.json().get("status") == "safety", r.text[:120])

    r = client.post("/api/journal", headers=auth, json={"text": "I want to die"})
    check("journal crisis phrase -> safety response", r.json().get("status") == "safety", r.text[:120])

    r = client.post("/api/mentor", headers=auth, json={"message": "I failed my exam and feel I am not capable."})
    check("mentor with no Gemini key -> 503 (not 500)", r.status_code == 503, f"{r.status_code} {r.text[:120]}")

    r = client.post("/api/vivekananda-vs-me", headers=auth, json={"view": "Failure proves I am not good enough."})
    check("vivekananda-vs-me with no Gemini key -> 503 (not 500)", r.status_code == 503, f"{r.status_code} {r.text[:120]}")

    r = client.get("/api/mentor/sessions", headers=auth)
    check("GET /api/mentor/sessions -> 200 list", r.status_code == 200 and isinstance(r.json(), list), r.text[:120])

    r = client.get("/api/mentor/sessions", headers={"X-Profile-Token": "wrong"})
    check("wrong token -> 404", r.status_code == 404, str(r.status_code))

failed = [n for ok, n in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
