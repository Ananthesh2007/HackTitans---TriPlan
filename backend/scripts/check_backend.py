"""One command that tells you whether the backend is healthy.

Checks three things and prints a single verdict:

1. Is a server running, and is it the current code?
2. Does the live server answer every endpoint correctly?
3. Does the offline test suite pass?

Usage:
    python scripts/check_backend.py
    python scripts/check_backend.py http://127.0.0.1:8000
    python scripts/check_backend.py --no-server     # skip the live checks

Exit code is 0 when everything is healthy, 1 otherwise.
"""

import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def colour(text, code):
    return f"{code}{text}{RESET}"


def line(status, label, detail=""):
    mark = {
        "ok": colour("PASS", GREEN),
        "bad": colour("FAIL", RED),
        "warn": colour("WARN", YELLOW),
        "skip": colour("SKIP", YELLOW),
    }[status]
    print(f"  [{mark}] {label}" + (f"  {DIM}{detail}{RESET}" if detail else ""))


def run(command, timeout=180):
    return subprocess.run(
        command, cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=timeout
    )


# --------------------------------------------------------------------------
print()
print(colour("TriPlan backend health check", BOLD))
print(DIM + "=" * 62 + RESET)

problems = []
warnings = []

# --------------------------------------------------------------------------
# 1. The live server
# --------------------------------------------------------------------------
server_url = "http://127.0.0.1:8000"
for i, arg in enumerate(sys.argv):
    if arg == "--no-server":
        server_url = None
    elif not arg.startswith("-") and i > 0:
        server_url = arg

print()
print(colour("1. Live server", BOLD))

if server_url is None:
    line("skip", "server checks", "skipped with --no-server")
else:
    try:
        import httpx
    except ImportError:
        line("bad", "httpx is installed", "run: pip install httpx")
        sys.exit(1)

    base = server_url.rstrip("/")

    try:
        health = httpx.get(f"{base}/health", timeout=10)
    except Exception as exc:
        line("bad", "server is reachable", f"{base} - {type(exc).__name__}")
        print()
        print(colour("  Start the backend:", YELLOW))
        print(colour(f"    cd {BACKEND_ROOT}", DIM))
        print(colour("    .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000", DIM))
        print()
        print(colour("  RESULT: FAIL - the server is not running.", RED + BOLD))
        sys.exit(1)

    line("ok", "server is reachable", f"{base} -> HTTP {health.status_code}")
    if health.status_code != 200:
        problems.append("health check did not return 200")

    body = health.json() if health.status_code == 200 else {}
    if body.get("status") == "ok":
        line("ok", "health reports ok", f"service={body.get('service')}")
    else:
        line("bad", "health reports ok", str(body))
        problems.append("health status is not ok")

    # Is the running server the current code?
    schema = httpx.get(f"{base}/openapi.json", timeout=10).json()
    raw = str(schema)
    if "retrieve_trip_api_trips__trip_id__get" in raw:
        line("ok", "running the current code", "route is named retrieve_trip")
    else:
        line("bad", "running the current code", "the route is still named get_trip")
        problems.append("the server is running stale code - restart it")

    paths = schema.get("paths", {})
    expected_paths = [
        "/health", "/api/trips", "/api/trips/{trip_id}",
        "/api/trips/{trip_id}/modify", "/api/trips/{trip_id}/budget",
        "/api/flights/search", "/api/flights/booking-link",
        "/api/hotels/search", "/api/hotels/booking-link",
        "/api/transport/search", "/api/weather",
    ]
    missing = [p for p in expected_paths if p not in paths]
    if missing:
        line("bad", "all endpoints are registered", f"missing: {missing}")
        problems.append(f"missing endpoints: {missing}")
    else:
        line("ok", "all endpoints are registered", f"{len(paths)} paths")

    # A real end-to-end trip, not just a health ping.
    payload = {
        "origin": "Mumbai", "destination": "Paris", "days": 3, "budget": 20000,
        "people": 2, "travel_date": "2026-12-01", "interests": ["culture"], "diet": "none",
    }
    created = httpx.post(f"{base}/api/trips", json=payload, timeout=30)
    if created.status_code != 200:
        line("bad", "a trip can be created", f"HTTP {created.status_code}")
        problems.append("trip creation failed")
    else:
        trip = created.json()
        trip_id = trip.get("trip_id")
        line("ok", "a trip can be created", f"id={trip_id}")

        if len(trip.get("itinerary", [])) == 3:
            line("ok", "the itinerary matches the request", "3 days")
        else:
            line("bad", "the itinerary matches the request",
                 f"expected 3 days, got {len(trip.get('itinerary', []))}")
            problems.append("the itinerary length does not match the requested days")

        if all(len(d.get("activities", [])) == 3 for d in trip.get("itinerary", [])):
            line("ok", "every day has 3 activities")
        else:
            line("bad", "every day has 3 activities")
            problems.append("a day does not have 3 activities")

        costs = trip.get("estimated_costs", {})
        lines = {k: v for k, v in costs.items() if k != "total"}
        if costs.get("total") == sum(lines.values()):
            line("ok", "the budget adds up", f"total {costs.get('total'):,.0f}")
        else:
            line("bad", "the budget adds up", f"{costs.get('total')} vs {sum(lines.values())}")
            problems.append("the estimated_costs total does not equal the sum of the lines")

        plan_sum = sum(
            a["estimated_cost"] for d in trip.get("itinerary", []) for a in d["activities"]
        )
        if costs.get("activities") == plan_sum * trip.get("people", 1):
            line("ok", "the budget agrees with the itinerary")
        else:
            line("bad", "the budget agrees with the itinerary",
                 f"{costs.get('activities')} vs {plan_sum * trip.get('people', 1)}")
            problems.append("the activities line does not match the itinerary")

        fetched = httpx.get(f"{base}/api/trips/{trip_id}", timeout=15)
        if fetched.status_code == 200:
            line("ok", "the trip can be read back", f"HTTP 200")
        else:
            line("bad", "the trip can be read back", f"HTTP {fetched.status_code}")
            problems.append("the created trip could not be read back")

        missing_trip = httpx.get(f"{base}/api/trips/does-not-exist", timeout=15)
        if missing_trip.status_code == 404:
            line("ok", "a missing trip returns 404")
        else:
            line("bad", "a missing trip returns 404", f"HTTP {missing_trip.status_code}")
            problems.append("a missing trip did not return 404")

        budget = httpx.post(f"{base}/api/trips/{trip_id}/budget", timeout=15)
        if budget.status_code == 200:
            line("ok", "the budget endpoint works")
        else:
            line("bad", "the budget endpoint works", f"HTTP {budget.status_code}")
            problems.append("the budget endpoint failed")

# --------------------------------------------------------------------------
# 2. The live smoke test
# --------------------------------------------------------------------------
print()
print(colour("2. Live smoke test", BOLD))

smoke = BACKEND_ROOT / "scripts" / "smoke_test.py"
if server_url is None:
    line("skip", "smoke test", "it needs a running server")
elif not smoke.exists():
    line("skip", "smoke test", "scripts/smoke_test.py is missing")
else:
    result = run([sys.executable, str(smoke), server_url])
    match = re.search(r"(\d+) passed, (\d+) failed", result.stdout)
    if match:
        passed, failed = int(match.group(1)), int(match.group(2))
        if failed == 0:
            line("ok", "every check passes", f"{passed} checks")
        else:
            line("bad", "every check passes", f"{passed} passed, {failed} failed")
            problems.append(f"{failed} smoke test checks failed")
            for name in re.findall(r"^  - (.+)$", result.stdout, re.M)[:10]:
                print(DIM + f"       {name}" + RESET)
    else:
        # The smoke test may have crashed before printing its summary.
        line("bad", "the smoke test ran", "it did not finish")
        problems.append("the smoke test did not report a result")
        for name in re.findall(r"^  \[FAIL\] (.+)$", result.stdout, re.M)[:10]:
            print(DIM + f"       {name}" + RESET)

# --------------------------------------------------------------------------
# 3. The offline test suite
# --------------------------------------------------------------------------
print()
print(colour("3. Offline test suite", BOLD))

if not (BACKEND_ROOT / "tests").exists():
    line("skip", "pytest suite", "tests/ is missing")
else:
    result = run([sys.executable, "-m", "pytest"], timeout=300)
    match = re.search(r"(\d+) passed", result.stdout)
    failed_match = re.search(r"(\d+) failed", result.stdout)
    if match:
        passed = int(match.group(1))
        failed = int(failed_match.group(1)) if failed_match else 0
        if failed == 0:
            line("ok", "every test passes", f"{passed} tests")
        else:
            line("bad", "every test passes", f"{passed} passed, {failed} failed")
            problems.append(f"{failed} pytest tests failed")
    else:
        line("bad", "pytest ran", result.stdout.strip()[-200:] or result.stderr[-300:])
        problems.append("pytest did not report a result")

# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------
print()
print(DIM + "=" * 62 + RESET)
if problems:
    print(colour("  RESULT: FAIL", RED + BOLD))
    for problem in problems:
        print(f"    - {problem}")
    print()
    print(colour("  Next steps:", YELLOW))
    if any("stale" in p or "not running" in p for p in problems):
        print(DIM + f"    cd {BACKEND_ROOT}" + RESET)
        print(DIM + "    .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000" + RESET)
    print()
    sys.exit(1)

print(colour("  RESULT: PASS - the backend is working correctly.", GREEN + BOLD))
print()
sys.exit(0)
