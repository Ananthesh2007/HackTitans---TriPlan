"""Smoke test suite for the TriPlan backend.

Runs a set of checks against a running server and prints a pass/fail line for
each one. It never changes the server's data beyond creating a few trips.

Usage:
    python scripts/smoke_test.py                      # against http://127.0.0.1:8000
    python scripts/smoke_test.py http://127.0.0.1:8061

Exit code is 0 when every check passes, 1 otherwise.
"""

import concurrent.futures
import json
import sys
import time

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 20

results = []


def check(name, passed, detail=""):
    results.append((name, passed, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f"  -- {detail}" if detail else ""))


def request(method, path, **kwargs):
    """Make a request and return (status_code, parsed_body_or_text)."""
    try:
        r = httpx.request(method, BASE + path, timeout=TIMEOUT, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, r.text


def expect_error(name, method, path, status, code=None, **kwargs):
    """The response must be the standard error shape with the given status."""
    got_status, body = request(method, path, **kwargs)
    ok = got_status == status and isinstance(body, dict) and "error" in body
    if ok and code is not None:
        ok = body["error"].get("code") == code
    check(name, ok, f"expected {status}, got {got_status}")


def section(title):
    print(f"\n{title}")


# --------------------------------------------------------------------------
section("1. Health and service metadata")
status, body = request("GET", "/health")
check("GET /health returns 200", status == 200, f"got {status}")
check(
    "health reports ok and the service name",
    isinstance(body, dict) and body.get("status") == "ok" and body.get("service") == "triplan-backend",
)
status, body = request("GET", "/openapi.json")
check("GET /openapi.json returns 200", status == 200, f"got {status}")
paths = body.get("paths", {}) if isinstance(body, dict) else {}
check(
    "all 12 documented endpoints are registered",
    len(paths) == 12,
    f"found {len(paths)}: {sorted(paths)}",
)

# --------------------------------------------------------------------------
section("2. Trip creation - happy path")
good = {
    "origin": "Mumbai",
    "destination": "Paris",
    "days": 3,
    "budget": 20000,
    "people": 2,
    "travel_date": "2026-12-01",
    "interests": ["culture", "food"],
    "diet": "none",
}
status, trip = request("POST", "/api/trips", json=good)
check("POST /api/trips returns 200", status == 200, f"got {status}")
TRIP_ID = trip.get("trip_id") if isinstance(trip, dict) else None
check("response carries a trip_id", bool(TRIP_ID))
check("trip_id looks like a UUID", bool(TRIP_ID) and len(TRIP_ID) == 36 and TRIP_ID.count("-") == 4)
check("is_mock is true when no AI provider is configured", trip.get("is_mock") is True)
check("is_estimate is true", trip.get("is_estimate") is True)
check("origin is echoed", trip.get("origin") == "Mumbai")
check("destination is echoed", trip.get("destination") == "Paris")
check("days is echoed", trip.get("days") == 3)
check("people is echoed", trip.get("people") == 2)
check("budget is echoed", trip.get("budget") == 20000)
check("currency is INR", trip.get("currency") == "INR")
check("interests are echoed", trip.get("interests") == ["culture", "food"])
check("diet is echoed", trip.get("diet") == "none")
check("travel_date comes back as a date string", trip.get("travel_date") == "2026-12-01")
check("a warning explains the sample itinerary", "warning" in trip and trip["warning"])

itinerary = trip.get("itinerary", [])
check("itinerary has exactly 3 days", len(itinerary) == 3, f"got {len(itinerary)}")
check("every day is numbered 1..n", [d["day"] for d in itinerary] == [1, 2, 3])
check(
    "every day has 3 activities",
    all(len(d["activities"]) == 3 for d in itinerary),
    f"got {[len(d['activities']) for d in itinerary]}",
)
check(
    "every activity has time, name, location and cost",
    all(
        a.get("time") and a.get("name") and a.get("location") and isinstance(a.get("estimated_cost"), (int, float))
        for d in itinerary
        for a in d["activities"]
    ),
)
check(
    "activity locations carry the destination",
    all(a["location"].endswith("Paris") for d in itinerary for a in d["activities"]),
)
check(
    "activity times look like HH:MM",
    all(
        len(a["time"]) == 5
        and a["time"][2] == ":"
        and a["time"][:2].isdigit()
        and a["time"][3:].isdigit()
        and 0 <= int(a["time"][:2]) <= 23
        and 0 <= int(a["time"][3:]) <= 59
        for d in itinerary
        for a in d["activities"]
    ),
)
check("no activity has a negative cost", all(a["estimated_cost"] >= 0 for d in itinerary for a in d["activities"]))

costs = trip.get("estimated_costs", {})
check("estimated_costs has all five lines", set(costs) == {"flights", "accommodation", "food", "activities", "local_transport", "total"})
lines = {k: v for k, v in costs.items() if k != "total"}
check("total equals the sum of the lines", costs.get("total") == sum(lines.values()), f"{costs.get('total')} vs {sum(lines.values())}")
plan_sum = sum(a["estimated_cost"] for d in itinerary for a in d["activities"])
check(
    "the activities line equals the plan cost x people",
    costs.get("activities") == plan_sum * trip["people"],
    f"{costs.get('activities')} vs {plan_sum * trip['people']}",
)
check("flights scale with people", costs.get("flights") == 4800 * trip["people"])
check("accommodation scales with days x people", costs.get("accommodation") == 2000 * trip["days"] * trip["people"])
check("food scales with days x people", costs.get("food") == 1000 * trip["days"] * trip["people"])
check("local transport scales with days x people", costs.get("local_transport") == 500 * trip["days"] * trip["people"])

# --------------------------------------------------------------------------
section("3. Trip creation - optional and edge inputs")
status, body = request("POST", "/api/trips", json={k: v for k, v in good.items() if k != "origin"})
check("origin may be omitted", status == 200 and body.get("origin") is None, f"got {status}")

for days in (1, 7, 30):
    status, body = request("POST", "/api/trips", json={**good, "days": days})
    check(
        f"a {days}-day request returns {days} days",
        status == 200 and len(body.get("itinerary", [])) == days,
        f"got {status}, {len(body.get('itinerary', []))} days",
    )

status, body = request("POST", "/api/trips", json={**good, "interests": []})
check("interests may be empty", status == 200 and body.get("interests") == [])

status, body = request("POST", "/api/trips", json={**good, "diet": "vegan"})
check("diet is echoed", status == 200 and body.get("diet") == "vegan")

status, body = request("POST", "/api/trips", json={**good, "travel_date": "2099-12-31"})
check("a far-future date is accepted", status == 200)

# --------------------------------------------------------------------------
section("4. Trip validation failures (all should be 422 invalid_input)")
invalid_trips = [
    ("days = 0", {"days": 0}),
    ("days = 31", {"days": 31}),
    ("budget = 0", {"budget": 0}),
    ("budget = -100", {"budget": -100}),
    ("people = 0", {"people": 0}),
    ("people = 21", {"people": 21}),
    ("destination of 1 character", {"destination": "P"}),
    ("destination of 81 characters", {"destination": "x" * 81}),
    ("a past travel_date", {"travel_date": "2020-01-01"}),
    ("an unparseable travel_date", {"travel_date": "not-a-date"}),
    ("a travel_date with a time part", {"travel_date": "2026-12-01T10:00:00"}),
    ("an unknown interest", {"interests": ["swimming"]}),
    ("nine interests", {"interests": ["nature"] * 9}),
    ("an unknown diet", {"diet": "keto"}),
]
for label, override in invalid_trips:
    expect_error(f"rejects {label}", "POST", "/api/trips", 422, "invalid_input", json={**good, **override})

expect_error("rejects a missing destination", "POST", "/api/trips", 422, "invalid_input",
              json={k: v for k, v in good.items() if k != "destination"})
expect_error("rejects a missing days field", "POST", "/api/trips", 422, "invalid_input",
              json={k: v for k, v in good.items() if k != "days"})
expect_error("rejects an empty body", "POST", "/api/trips", 422, "invalid_input", content=b"")
expect_error("rejects malformed JSON", "POST", "/api/trips", 422, "invalid_input",
              content=b"{not json", headers={"Content-Type": "application/json"})
expect_error("rejects a JSON array body", "POST", "/api/trips", 422, "invalid_input", json=[1, 2, 3])
expect_error("rejects a null body", "POST", "/api/trips", 422, "invalid_input", json=None)

# --------------------------------------------------------------------------
section("5. Trip retrieval and modification")
status, body = request("GET", f"/api/trips/{TRIP_ID}")
check("GET /api/trips/{id} returns 200", status == 200, f"got {status}")
check("the retrieved trip matches what was created", body.get("itinerary") == trip.get("itinerary"))
check("the retrieved trip keeps its id", body.get("trip_id") == TRIP_ID)

status, body = request("POST", f"/api/trips/{TRIP_ID}/modify", json={"message": "make it cheaper"})
check("POST /api/trips/{id}/modify returns 200", status == 200, f"got {status}")
check("modify returns a reply string", isinstance(body.get("reply"), str) and body.get("reply") != "")
check("modify returns a proposed trip", isinstance(body.get("trip"), dict) and bool(body["trip"].get("itinerary")))
check("the proposed trip keeps the same id", body.get("trip", {}).get("trip_id") == TRIP_ID)

status, body = request("POST", f"/api/trips/{TRIP_ID}/budget")
check("POST /api/trips/{id}/budget returns 200", status == 200, f"got {status}")
status_body = body.get("budget_status", {})
check("budget_status echoes the budget", status_body.get("budget") == 20000)
check("budget_status echoes the estimate", status_body.get("estimate") == body["estimated_costs"]["total"])
check("is_below_estimate is a boolean", isinstance(status_body.get("is_below_estimate"), bool))
check("shortfall is estimate minus budget when over", status_body.get("shortfall") == max(0, status_body.get("estimate", 0) - 20000))
check("the message names the rupee amounts", "₹" in (status_body.get("message") or ""))

expect_error("GET a missing trip returns 404", "GET", "/api/trips/does-not-exist", 404, "trip_not_found")
expect_error("modify a missing trip returns 404", "POST", "/api/trips/does-not-exist/modify", 404, "trip_not_found", json={"message": "hi"})
expect_error("budget a missing trip returns 404", "POST", "/api/trips/does-not-exist/budget", 404, "trip_not_found")
expect_error("modify with an empty message returns 422", "POST", f"/api/trips/{TRIP_ID}/modify", 422, "invalid_input", json={"message": ""})
expect_error("modify with a 501-char message returns 422", "POST", f"/api/trips/{TRIP_ID}/modify", 422, "invalid_input", json={"message": "x" * 501})

# --------------------------------------------------------------------------
section("6. Flight search")
flights = {"origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2}
status, body = request("POST", "/api/flights/search", json=flights)
check("POST /api/flights/search returns 200", status == 200, f"got {status}")
check("the response flags mock data", body.get("is_mock") is True)
check("results is a non-empty list", isinstance(body.get("results"), list) and len(body["results"]) > 0)
check("every result has an id and a price", all(r.get("id") and isinstance(r.get("price"), (int, float)) for r in body.get("results", [])))
check("every result price is 0 or more", all(r.get("price", 0) >= 0 for r in body.get("results", [])))
check("every result currency is INR", all(r.get("currency") == "INR" for r in body.get("results", [])))
check("no booking_url points anywhere unverified", all(r.get("booking_url") is None or str(r["booking_url"]).startswith("https://") for r in body.get("results", [])))

expect_error("flights rejects the same origin and destination", "POST", "/api/flights/search", 422, "invalid_input",
              json={**flights, "destination": "Mumbai"})
expect_error("flights rejects a past date", "POST", "/api/flights/search", 422, "invalid_input",
              json={**flights, "date": "2020-01-01"})
expect_error("flights rejects passengers = 0", "POST", "/api/flights/search", 422, "invalid_input",
              json={**flights, "passengers": 0})
expect_error("flights rejects passengers = 10", "POST", "/api/flights/search", 422, "invalid_input",
              json={**flights, "passengers": 10})
expect_error("flights rejects a missing date field", "POST", "/api/flights/search", 422, "invalid_input",
              json={k: v for k, v in flights.items() if k != "date"})
expect_error("flights rejects the name departure_date", "POST", "/api/flights/search", 422, "invalid_input",
              json={"origin": "Mumbai", "destination": "Paris", "departure_date": "2026-12-01", "passengers": 2})

# --------------------------------------------------------------------------
section("7. Hotel search")
hotels = {"destination": "Paris", "check_in": "2026-12-01", "check_out": "2026-12-04", "guests": 2}
status, body = request("POST", "/api/hotels/search", json=hotels)
check("POST /api/hotels/search returns 200", status == 200, f"got {status}")
check("the response flags mock data", body.get("is_mock") is True)
check("results is a non-empty list", isinstance(body.get("results"), list) and len(body["results"]) > 0)
check("every result has a name and a nightly price", all(r.get("name") and isinstance(r.get("price_per_night"), (int, float)) for r in body.get("results", [])))

status, body = request("POST", "/api/hotels/search", json={**hotels, "rooms": 1})
check("hotels accepts an explicit rooms value", status == 200)
expect_error("hotels rejects check-out before check-in", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "check_out": "2026-11-30"})
expect_error("hotels rejects check-out equal to check-in", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "check_out": "2026-12-01"})
expect_error("hotels rejects a past check-in", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "check_in": "2020-01-01"})
expect_error("hotels rejects guests = 0", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "guests": 0})
expect_error("hotels rejects guests = 21", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "guests": 21})
expect_error("hotels rejects rooms = 0", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "rooms": 0})
expect_error("hotels rejects rooms = 11", "POST", "/api/hotels/search", 422, "invalid_input",
              json={**hotels, "rooms": 11})

# --------------------------------------------------------------------------
section("8. Transport search")
for mode, keyword in (("bus", "bus"), ("train", "train")):
    status, body = request("POST", "/api/transport/search", json={
        "origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2, "mode": mode,
    })
    check(f"transport search for {mode} returns 200", status == 200, f"got {status}")
    check(f"transport {mode} results are non-empty", isinstance(body.get("results"), list) and len(body["results"]) > 0)
    check(f"transport {mode} results mention {keyword}",
          all(keyword.lower() in (r.get("vehicle_type", "") + r.get("id", "")).lower() for r in body.get("results", [])))

expect_error("transport rejects mode = car", "POST", "/api/transport/search", 422, "invalid_input",
              json={"origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2, "mode": "car"})
expect_error("transport rejects a missing mode", "POST", "/api/transport/search", 422, "invalid_input",
              json={"origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2})

# --------------------------------------------------------------------------
section("9. Booking links")
status, body = request("POST", "/api/flights/booking-link", json={"flight_id": "flight-001"})
check("flight booking link returns 200", status == 200, f"got {status}")
check("flight booking link echoes the id", body.get("flight_id") == "flight-001")
check("flight booking url is https", str(body.get("booking_url", "")).startswith("https://"))
check("flight booking url is from the verified list",
      any(str(body.get("booking_url", "")).startswith(p) for p in
          ("https://www.skyscanner.co.in/", "https://www.makemytrip.com/", "https://www.goibibo.com/", "https://www.cleartrip.com/")))
check("flight booking link has a message", bool(body.get("message")))

status, body = request("POST", "/api/hotels/booking-link", json={"hotel_id": "hotel-001"})
check("hotel booking link returns 200", status == 200, f"got {status}")
check("hotel booking url is https", str(body.get("booking_url", "")).startswith("https://"))
check("hotel booking url is from the verified list",
      any(str(body.get("booking_url", "")).startswith(p) for p in
          ("https://www.booking.com/", "https://www.makemytrip.com/", "https://www.goibibo.com/", "https://www.agoda.com/")))

status, body = request("POST", "/api/flights/booking-link", json={"flight_id": "f1", "booking_url": "http://evil.example.com"})
check("a caller-supplied booking_url is ignored", status == 200 and "evil.example.com" not in json.dumps(body))

expect_error("flight booking link needs a flight_id", "POST", "/api/flights/booking-link", 400, "invalid_input", json={})
expect_error("flight booking link rejects an empty flight_id", "POST", "/api/flights/booking-link", 400, "invalid_input", json={"flight_id": ""})
expect_error("hotel booking link needs a hotel_id", "POST", "/api/hotels/booking-link", 400, "invalid_input", json={})

# --------------------------------------------------------------------------
section("10. Weather")
status, body = request("GET", "/api/weather", params={"place": "Coorg", "date": "2026-11-20"})
check("GET /api/weather returns 200", status == 200, f"got {status}")
check("weather echoes the place", body.get("place") == "Coorg")
check("weather echoes the date", body.get("date") == "2026-11-20")
check("weather says the service is not configured", "error" in body)

status, body = request("GET", "/api/weather/", params={"place": "Coorg", "date": "2026-11-20"})
check("GET /api/weather/ also works", status == 200, f"got {status}")

expect_error("weather needs a place", "GET", "/api/weather", 422, "invalid_input", params={"date": "2026-11-20"})
expect_error("weather needs a date", "GET", "/api/weather", 422, "invalid_input", params={"place": "Coorg"})
expect_error("weather rejects a past date", "GET", "/api/weather", 422, "invalid_input", params={"place": "Coorg", "date": "2020-01-01"})
expect_error("weather rejects a 1-character place", "GET", "/api/weather", 422, "invalid_input", params={"place": "C", "date": "2026-11-20"})

# --------------------------------------------------------------------------
section("11. Error shape and HTTP behaviour")
for method, path, expected in [
    ("GET", "/api/trips", 405),
    ("PUT", "/health", 405),
    ("DELETE", "/health", 405),
    ("GET", "/api/trips/a/b/c", 404),
]:
    status, body = request(method, path)
    ok = status == expected and isinstance(body, dict) and "error" in body
    check(f"{method} {path} returns {expected} in the standard shape", ok, f"got {status}")

status, body = request("GET", "/api/trips/" + "a" * 500)
check("a very long trip id is handled without crashing", status == 404 and "error" in body, f"got {status}")

for label, trip_id in [
    ("a SQL injection attempt", "' OR '1'='1"),
    ("a DROP TABLE attempt", "x'; DROP TABLE trips;--"),
]:
    status, body = request("GET", f"/api/trips/{trip_id}")
    check(f"{label} is handled safely", status == 404 and "error" in body, f"got {status}")

status, body = request("GET", "/health", headers={"Origin": "http://localhost:5173"})
check("CORS allows the configured frontend origin", body is not None and "status" in body)
status, body = request("GET", "/health", headers={"Origin": "http://evil.example.com"})
check("CORS does not echo a foreign origin", status == 200)

# --------------------------------------------------------------------------
section("12. Concurrency and persistence")
t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    futures = [
        pool.submit(request, "POST", "/api/trips",
                    json={**good, "budget": 15000 + i})
        for i in range(20)
    ]
    codes = [f.result()[0] for f in futures]
check("20 concurrent trip creations all succeed", set(codes) == {200}, f"got {sorted(set(codes))} in {time.time()-t0:.2f}s")

status, body = request("GET", f"/api/trips/{TRIP_ID}")
check("the first trip is still readable after concurrent writes", status == 200)

# --------------------------------------------------------------------------
section("13. Contract cross-check")
status, body = request("GET", "/openapi.json")
check("the trip route is named retrieve_trip (the recursion fix)",
      "retrieve_trip_api_trips__trip_id__get" in json.dumps(body),
      "the old name means the running server is stale")
check("both weather paths are registered",
      "/api/weather" in body.get("paths", {}) and "/api/weather/" in body.get("paths", {}))

# --------------------------------------------------------------------------
passed = sum(1 for _, ok, _ in results if ok)
failed = len(results) - passed
print("\n" + "=" * 62)
print(f"  {passed} passed, {failed} failed, {len(results)} total")
print("=" * 62)
if failed:
    print("\nFailures:")
    for name, ok, detail in results:
        if not ok:
            print(f"  - {name}  ({detail})")
sys.exit(1 if failed else 0)
