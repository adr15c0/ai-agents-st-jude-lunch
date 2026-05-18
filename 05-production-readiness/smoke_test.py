"""End-to-end smoke test for Demo 5 \u2014 spawn uvicorn, hit /healthz and /chat, tear down."""
from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx
from dotenv import load_dotenv

# Force UTF-8 so the Windows console can print model output with smart quotes/dashes.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


PORT = int(os.environ.get("DEMO5_SMOKE_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"


def wait_for_healthz(timeout_s: float = 45.0) -> None:
    deadline = time.time() + timeout_s
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE}/healthz", timeout=2.0)
            if r.status_code == 200:
                print("healthz:", r.json())
                return
        except Exception as ex:
            last_err = ex
        time.sleep(1)
    raise RuntimeError(f"server did not become healthy in {timeout_s:.0f}s ({last_err})")


def main() -> None:
    load_dotenv()
    # Sanity-check the env so the subprocess fails fast rather than the smoke test.
    os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT), "--log-level", "warning"],
    )
    try:
        wait_for_healthz()

        print("\n=== POST /chat #1 ===")
        r1 = httpx.post(
            f"{BASE}/chat",
            json={"message": "In one sentence, what does TP53 do?"},
            timeout=120,
        ).raise_for_status().json()
        print(f"session_id: {r1['session_id']}")
        print(f"reply     : {r1['reply'][:240]}")

        print("\n=== POST /chat #2 (same session) ===")
        r2 = httpx.post(
            f"{BASE}/chat",
            json={"message": "And what diseases is it tied to?", "session_id": r1["session_id"]},
            timeout=120,
        ).raise_for_status().json()
        print(f"session_id: {r2['session_id']}")
        print(f"reply     : {r2['reply'][:300]}")

        assert r1["session_id"] == r2["session_id"], "session_id should round-trip"
        print("\nsmoke test PASSED")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
