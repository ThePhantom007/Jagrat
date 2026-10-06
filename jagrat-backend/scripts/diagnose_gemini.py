"""Find out WHY the main-model call fails. Makes at most 4 small Gemini calls, each time-limited.

    python scripts/diagnose_gemini.py
Optionally test another main model:  set GEMINI_MODEL=gemini-3.5-flash   (then run again)
"""
import concurrent.futures as cf
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.schemas import MentorGeneration, RiskResult  # noqa: E402
from app.services.gemini import GeminiService  # noqa: E402

settings = get_settings()
if not settings.gemini_api_key:
    sys.exit("GEMINI_API_KEY is not set.")
svc = GeminiService()
print(f"main model: {settings.gemini_model} | fast model: {settings.gemini_fast_model} | timeout: {settings.gemini_timeout_seconds}s\n")


def attempt(label, fn, limit=75):
    start = time.time()
    pool = cf.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn)
    try:
        future.result(timeout=limit)
        print(f"PASS  {label}  ({time.time() - start:.1f}s)")
        return True
    except cf.TimeoutError:
        print(f"HANG  {label}  (no answer after {limit}s)")
    except Exception as exc:  # noqa: BLE001
        cause = exc.__cause__ or exc
        print(f"FAIL  {label}  ({time.time() - start:.1f}s)\n      {type(cause).__name__}: {str(cause)[:500]}")
    pool.shutdown(wait=False, cancel_futures=True)
    return False


system = "Return JSON only."
attempt("1) main model, tiny schema (RiskResult)",
        lambda: svc.generate(system_instruction=system, prompt="I am nervous about my exam.", schema=RiskResult))
attempt("2) fast model, big schema (MentorGeneration)",
        lambda: svc.generate(system_instruction=system, prompt="Fill every field briefly; quote_id null. Context: student nervous about exam.", schema=MentorGeneration, fast=True))
attempt("3) main model, big schema (MentorGeneration)",
        lambda: svc.generate(system_instruction=system, prompt="Fill every field briefly; quote_id null. Context: student nervous about exam.", schema=MentorGeneration))
print("\nDone (3 Gemini calls at most).")
os._exit(0)
