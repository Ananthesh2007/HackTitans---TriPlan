# API Testing Cheat Sheet

Every command below is copy-paste ready. The server is expected at
`http://127.0.0.1:8000`.

> **PowerShell note:** `curl` is an alias for `Invoke-WebRequest`, which throws
> on any non-2xx status and prints a red error even when the response body is
> correct. Use `curl.exe` for the real binary, or add `-SkipHttpErrorCheck` to
> `Invoke-WebRequest`.

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

The automated suite below covers all of this at once:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/smoke_test.py
```

---

## 1. Health and metadata

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s http://127.0.0.1:8000/openapi.json
```

## 2. Create a trip

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/trips `
  -H "Content-Type: application/json" `
  -d '{
        "origin": "Mumbai",
        "destination": "Paris",
        "days": 3,
        "budget": 20000,
        "people": 2,
        "travel_date": "2026-12-01",
        "interests": ["culture", "food"],
        "diet": "none"
      }'
```

Save the returned `trip_id` for the calls below:

```powershell
$TID = "paste-the-trip-id-here"
```

## 3. Retrieve, modify and budget

```powershell
curl.exe -s http://127.0.0.1:8000/api/trips/$TID
curl.exe -s -X POST http://127.0.0.1:8000/api/trips/$TID/modify -H "Content-Type: application/json" -d '{"message":"make it cheaper"}'
curl.exe -s -X POST http://127.0.0.1:8000/api/trips/$TID/budget
```

## 4. Searches

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/flights/search -H "Content-Type: application/json" -d '{"origin":"Mumbai","destination":"Paris","date":"2026-12-01","passengers":2}'
curl.exe -s -X POST http://127.0.0.1:8000/api/hotels/search -H "Content-Type: application/json" -d '{"destination":"Paris","check_in":"2026-12-01","check_out":"2026-12-04","guests":2}'
curl.exe -s -X POST http://127.0.0.1:8000/api/transport/search -H "Content-Type: application/json" -d '{"origin":"Mumbai","destination":"Paris","date":"2026-12-01","passengers":2,"mode":"train"}'
```

## 5. Booking links

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/flights/booking-link -H "Content-Type: application/json" -d '{"flight_id":"flight-001"}'
curl.exe -s -X POST http://127.0.0.1:8000/api/hotels/booking-link -H "Content-Type: application/json" -d '{"hotel_id":"hotel-001"}'
```

## 6. Weather

```powershell
curl.exe -s "http://127.0.0.1:8000/api/weather?place=Coorg&date=2026-11-20"
```

---

# Error cases to test

Every error must come back in this shape, with no stack trace and no crash:

```json
{"error": {"code": "snake_case_code", "message": "Human-readable", "details": []}}
```

## Validation errors (expect 422 `invalid_input`)

```powershell
# days out of range
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"Paris","days":0,"budget":100,"people":1,"travel_date":"2026-12-01"}'

# budget not positive
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"Paris","days":3,"budget":-100,"people":1,"travel_date":"2026-12-01"}'

# people out of range
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"Paris","days":3,"budget":100,"people":21,"travel_date":"2026-12-01"}'

# destination too short
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"P","days":3,"budget":100,"people":1,"travel_date":"2026-12-01"}'

# travel date in the past
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"Paris","days":3,"budget":100,"people":1,"travel_date":"2020-01-01"}'

# unknown interest
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"destination":"Paris","days":3,"budget":100,"people":1,"travel_date":"2026-12-01","interests":["swimming"]}'

# missing required field
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{"days":3,"budget":100,"people":1,"travel_date":"2026-12-01"}'

# malformed JSON
curl.exe -s -X POST http://127.0.0.1:8000/api/trips -H "Content-Type: application/json" -d '{not json'

# wrong field name (the contract uses "date", not "departure_date")
curl.exe -s -X POST http://127.0.0.1:8000/api/flights/search -H "Content-Type: application/json" -d '{"origin":"Mumbai","destination":"Paris","departure_date":"2026-12-01","passengers":2}'
```

## Not found (expect 404 `trip_not_found`)

```powershell
curl.exe -s http://127.0.0.1:8000/api/trips/does-not-exist
curl.exe -s -X POST http://127.0.0.1:8000/api/trips/does-not-exist/modify -H "Content-Type: application/json" -d '{"message":"hi"}'
curl.exe -s -X POST http://127.0.0.1:8000/api/trips/does-not-exist/budget
```

## Bad requests (expect 400 `invalid_input`)

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/flights/booking-link -H "Content-Type: application/json" -d '{}'
curl.exe -s -X POST http://127.0.0.1:8000/api/hotels/booking-link -H "Content-Type: application/json" -d '{"hotel_id":""}'
```

## Wrong method (expect 405 `method_not_allowed`)

```powershell
curl.exe -s http://127.0.0.1:8000/api/trips
curl.exe -s -X DELETE http://127.0.0.1:8000/health
```

## Injection and traversal (expect 404, no crash, table intact)

```powershell
curl.exe -s "http://127.0.0.1:8000/api/trips/' OR '1'='1"
curl.exe -s "http://127.0.0.1:8000/api/trips/x'; DROP TABLE trips;--"
curl.exe -s http://127.0.0.1:8000/api/trips/../../etc/passwd
```

## CORS

```powershell
curl.exe -s -D- -o NUL -H "Origin: http://localhost:5173" http://127.0.0.1:8000/health | findstr access-control
curl.exe -s -D- -o NUL -H "Origin: http://evil.example.com" http://127.0.0.1:8000/health | findstr access-control
```

The first must echo `http://localhost:5173`; the second must echo nothing.

---

# AI provider scenarios

`LLM_API_KEY` is empty in `.env`, so the backend runs on the built-in sample
itinerary. To test the real provider path, set a key in `.env` and restart.

| Scenario | How to trigger | Expected |
|---|---|---|
| No key configured | default `.env` | 200, `is_mock: true`, `warning` explains it |
| Provider down | set `LLM_BASE_URL` to a dead port | 200, falls back to mock + warning |
| Provider times out | set `LLM_TIMEOUT_SECONDS=1` | 200, falls back to mock + warning |
| Provider returns garbage | point at a stub that returns plain text | 200, falls back to mock + warning |
| Provider returns the wrong day count | stub returns 1 day for a 3-day trip | **502 `invalid_ai_output`** |
| Provider returns valid JSON | stub returns a valid itinerary | 200, `is_mock: false` |

The last two are the interesting ones: a schema mismatch is rejected with a
502, while a transport failure falls back to the sample plan.

---

# Things worth watching

**The budget never scales with the user's budget.** The estimate uses fixed
per-person rates, so a budget of ₹1 still produces a full estimate. The budget
is only compared against the estimate. That is by design, not a bug.

**The `activities` line now equals the plan cost x people**, so it moves when
the itinerary changes. If you ever see it disagree with the itinerary card,
one of them is stale.

**The server can wedge with `--reload` on Windows.** If a reload fails, the
worker stops answering while still holding port 8000, and every request
hangs. The recovery is:

```powershell
taskkill /PID <worker-pid> /T /F
```

Running without `--reload` avoids it entirely.

**`trips.db` grows with every test.** It is gitignored, so it never gets
committed, but it is worth clearing before a demo:

```powershell
Remove-Item backend\data\trips.db
```

The next request recreates it automatically.
