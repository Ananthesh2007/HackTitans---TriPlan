# Integration Testing Guide (Oct 22, 2026)

This guide covers the integration tests required for the TriPlan backend as per the Sprint 4 timetable.

## Test Objectives

Verify that every error scenario returns clear JSON and nothing crashes. All endpoints must handle failures gracefully.

## How to Run the Tests

The automated suite lives in `backend/tests/` and runs the app in-process, so **no server needs to be running**.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Expected output:

```
132 passed in 24.06s
```

Other useful invocations:

```powershell
# verbose, one line per test
.\.venv\Scripts\python.exe -m pytest -v

# a single file
.\.venv\Scripts\python.exe -m pytest tests/test_failures.py -v

# a single test
.\.venv\Scripts\python.exe -m pytest tests/test_trips.py::TestBudget -v

# stop on the first failure
.\.venv\Scripts\python.exe -m pytest -x
```

There is also a server-level smoke test that runs against a running instance and
needs no pytest:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_test.py
```

| File | What it covers |
|---|---|
| `tests/test_trips.py` | Trip creation, validation, retrieval, modification, budget |
| `tests/test_search.py` | Flight, hotel and transport search, booking links, weather |
| `tests/test_errors.py` | Error format, CORS, concurrency, contract guards |
| `tests/test_failures.py` | AI provider failures and database failures |
| `scripts/smoke_test.py` | The same checks against a live server (145 checks) |

## Test Categories

### 1. AI Provider Failures

The AI tests point the app at a stub provider that misbehaves on purpose. The
app is started in a separate process because the provider settings are read at
import time.

#### Test: Invalid AI Output
```
Scenario: LLM returns malformed JSON
Expected: 200, the sample itinerary, is_mock=true and a warning
Endpoint: POST /api/trips
```
A provider that answers with unusable text is a *transport* problem, not a
schema problem, so the user still gets a plan.

#### Test: LLM Timeout
```
Scenario: AI provider takes too long
Expected: 200, the sample itinerary, is_mock=true and a warning
Endpoint: POST /api/trips
```

#### Test: Invalid API Key
```
Scenario: LLM_API_KEY is wrong or expired (provider answers 401)
Expected: 200, the sample itinerary, is_mock=true and a warning
Endpoint: POST /api/trips
```
The key is never logged and never appears in the response.

#### Test: Schema Mismatch
```
Scenario: LLM returns valid JSON that does not match the agreed schema
         (wrong number of days, or an activity with no name)
Expected: 502 with code "invalid_ai_output" and the issues listed
Endpoint: POST /api/trips
```
This is deliberately different from the cases above: the model answered, but
the answer cannot be used, so it is rejected instead of being silently
replaced.

#### Test: No API Key Configured
```
Scenario: LLM_API_KEY is empty, or FORCE_MOCK_AI is true
Expected: 200, the sample itinerary, is_mock=true and a warning
Endpoint: POST /api/trips
```

### 2. Database Failures

#### Test: Database File Corrupted
```
Scenario: trips.db contains garbage instead of a SQLite file
Expected: 200, the trip is created in memory, and the response warns
          "Trip created but not persisted. Data may be lost on server restart."
Endpoint: POST /api/trips
```

#### Test: Database File Locked
```
Scenario: another process holds an exclusive lock on trips.db
Expected: 200, the trip is created in memory, and the response warns
Endpoint: POST /api/trips
```

#### Test: Database Unavailable
```
Scenario: the database cannot be opened at all
Expected: 200 with the same warning, never a 500
Endpoint: POST /api/trips
```

#### Test: Disk Full
```
Scenario: no space left on device
Expected: the save fails, the trip is still returned, and the response warns
Endpoint: POST /api/trips
```

#### Test: Persistence Across Restarts
```
Scenario: create a trip, then read it back from a separate process
Expected: 200 with the same itinerary
Endpoint: GET /api/trips/{trip_id}
```
This is the reason the backend uses SQLite rather than the in-memory store.

### 3. External Provider Failures

#### Test: Flight Search Provider Down
```
Scenario: flight search API is unreachable
Expected: 200 with mock results and is_mock=true
Endpoint: POST /api/flights/search
```
No flight provider is integrated yet, so the endpoint always returns mock data
with the flag set.

#### Test: Hotel Search Provider Down
```
Scenario: hotel search API returns 500
Expected: 200 with mock results and is_mock=true
Endpoint: POST /api/hotels/search
```

#### Test: Weather Service Unavailable
```
Scenario: no weather provider is configured
Expected: 200 with {"place", "date", "error": "Weather service not configured."}
Endpoint: GET /api/weather
```
The endpoint never invents weather data for a real place.

### 4. Validation Failures

#### Test: Invalid Trip Request
```
Scenario: days=0, budget=-100, people=0
Expected: 422 with code "invalid_input" and a field detail per problem
Endpoint: POST /api/trips
```

#### Test: Malformed JSON
```
Scenario: request body is not valid JSON
Expected: 422 with code "invalid_input"
Endpoint: POST /api/trips
```
Note: this is **422**, not 400. FastAPI turns an unparseable body into a
request validation error, and the backend maps every validation error to 422.

#### Test: Missing Required Fields
```
Scenario: destination field missing
Expected: 422 with code "invalid_input" listing every missing field
Endpoint: POST /api/trips
```

#### Test: Past Travel Date
```
Scenario: travel_date is before today
Expected: 422 "Choose today or a later date."
Endpoint: POST /api/trips
```

### 5. Booking Link Validation

#### Test: Unverified URL
```
Scenario: a booking_url that is not in the verified allowlist is sent by the caller
Expected: it is ignored; the response contains a verified provider URL
Endpoint: POST /api/flights/booking-link
```

#### Test: Non-HTTPS URL
```
Scenario: a caller passes http:// instead of https://
Expected: it is ignored; the response contains an https:// URL
Endpoint: POST /api/hotels/booking-link
```

#### Test: Missing Id
```
Scenario: flight_id or hotel_id is missing or empty
Expected: 400 with code "invalid_input"
Endpoint: POST /api/flights/booking-link, POST /api/hotels/booking-link
```

### 6. Trip Modification Failures

#### Test: Trip Not Found
```
Scenario: modify a non-existent trip_id
Expected: 404 with code "trip_not_found"
Endpoint: POST /api/trips/{trip_id}/modify
```

#### Test: Invalid Modification Message
```
Scenario: the message is empty or longer than 500 characters
Expected: 422 with code "invalid_input"
Endpoint: POST /api/trips/{trip_id}/modify
```

#### Test: Invalid Revised Plan
```
Scenario: the revision produces an invalid itinerary
Expected: 422 with code "invalid_plan" and the issues listed
Endpoint: POST /api/trips/{trip_id}/modify
```

### 7. Security and Robustness

#### Test: Injection and Traversal
```
Scenario: a trip_id containing SQL, a path traversal, or a very long string
Expected: 404, no crash, and the trips table is untouched
Endpoint: GET /api/trips/{trip_id}
```

#### Test: Wrong HTTP Method
```
Scenario: GET /api/trips, or PUT /health
Expected: 405 with code "method_not_allowed"
Endpoint: any
```

#### Test: Concurrent Requests
```
Scenario: 20 trip creations run at the same time
Expected: all 20 return 200 with unique trip ids, and earlier trips stay readable
Endpoint: POST /api/trips
```

#### Test: CORS
```
Scenario: a request from an origin that is not in FRONTEND_ORIGINS
Expected: the response does not echo that origin
Endpoint: any
```

## Success Criteria

✅ Every error returns JSON in the standard format:
```json
{
  "error": {
    "code": "snake_case_error_code",
    "message": "User-friendly message",
    "details": []  // optional
  }
}
```

✅ No server crashes (500 errors are caught and handled)
✅ All database failures fall back gracefully
✅ External provider failures return mock data or clear alternatives
✅ Invalid requests return 422 with validation details
✅ Missing trips return 404
✅ Booking links are validated against allowlist
✅ Error messages never leak a stack trace or an internal path

## Test Results - Oct 22, 2026

Run with `.\.venv\Scripts\python.exe -m pytest` from `backend/`.
Result: **132 passed, 0 failed.**

### AI Provider Failures
- [x] Invalid AI output: PASS - 200, falls back to the sample plan with a warning
- [x] LLM timeout: PASS - 200, falls back to the sample plan with a warning
- [x] Invalid API key (401): PASS - 200, falls back to the sample plan with a warning
- [x] Provider unreachable: PASS - 200, falls back to the sample plan with a warning
- [x] Empty answer: PASS - 200, falls back to the sample plan with a warning
- [x] Schema mismatch (wrong day count): PASS - 502 `invalid_ai_output` with issues listed
- [x] Schema mismatch (missing fields): PASS - 502 `invalid_ai_output` with issues listed
- [x] No API key configured: PASS - 200, sample plan with a warning

### Database Failures
- [x] Database corrupted: PASS - 200, in-memory fallback, warning says it was not persisted
- [x] Database locked: PASS - 200, in-memory fallback, warning says it was not persisted
- [x] Database unavailable: PASS - 200, no 500
- [x] Persistence across processes: PASS - the trip is readable from a new process

### External Provider Failures
- [x] Flight search down: PASS - 200 with mock results and is_mock=true
- [x] Hotel search down: PASS - 200 with mock results and is_mock=true
- [x] Weather unavailable: PASS - 200 with the "not configured" body, no invented data

### Validation Failures
- [x] Invalid trip request: PASS - 422 with a detail per field
- [x] Malformed JSON: PASS - 422 `invalid_input`
- [x] Missing fields: PASS - 422 listing every missing field
- [x] Past travel date: PASS - 422 with a clear message

### Booking Link Validation
- [x] Unverified URL: PASS - ignored, a verified URL is returned
- [x] Non-HTTPS URL: PASS - ignored, an https URL is returned
- [x] Missing id: PASS - 400 `invalid_input`

### Trip Modification Failures
- [x] Trip not found: PASS - 404 `trip_not_found`
- [x] Invalid modification message: PASS - 422 `invalid_input`

### Security and Robustness
- [x] SQL injection in trip_id: PASS - 404, table intact
- [x] Path traversal: PASS - 404, no crash
- [x] Very long trip_id: PASS - 404, no crash
- [x] Wrong HTTP method: PASS - 405 `method_not_allowed`
- [x] 20 concurrent creations: PASS - all 200, unique ids, earlier trips still readable
- [x] CORS: PASS - a foreign origin is not echoed

### Critical Issues Found
None. The earlier `get_trip` recursion bug (which returned HTTP 500 for every
trip lookup) is fixed: the route handler is now named `retrieve_trip`, and
`tests/test_errors.py::TestContract` fails if it ever regresses.

### Non-Critical Issues
1. The budget estimate uses fixed per-person rates, so it does not scale with
   the user's stated budget. The budget is only compared against the estimate.
   This is by design, not a bug.
2. `trips.db` grows with every trip created during testing. It is gitignored,
   so it is never committed, but it should be cleared before a demo:
   `Remove-Item backend\data\trips.db`
3. With `--reload` on Windows, a failed reload can leave the worker holding
   port 8000 while answering nothing. Recovery is `taskkill /PID <pid> /T /F`.
   Running without `--reload` avoids it.
