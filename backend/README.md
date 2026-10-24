# TriPlan Backend

The FastAPI service behind TriPlan. It generates and modifies itineraries,
works out the estimated budget, and serves the flight, bus/train and hotel
search endpoints that the frontend pages use.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. The interactive docs are
at `http://localhost:8000/docs`.

The backend runs on the built-in sample itinerary until an AI provider is
configured, so it works with no key at all.

## Environment Variables

See `.env.example` for all required variables. Key variables:

- `LLM_PROVIDER`: `"openai"`, `"gemini"`, or `"none"`
- `LLM_API_KEY`: Your API key (never commit this)
- `LLM_TIMEOUT_SECONDS`: `15` (optimized for fast responses)
- `FRONTEND_ORIGINS`: Comma-separated list of allowed origins
- `MAPS_PROVIDER`: `"osm"` (OpenStreetMap, no key needed), `"google"`, or `"none"`
- `MAPS_API_KEY`: Only for `"google"` (never commit this)
- `AMADEUS_CLIENT_ID`: For live flight data (optional)
- `AMADEUS_CLIENT_SECRET`: For live flight data (optional)
- `TAVILY_API_KEY`: For live hotel data (optional)

Every key is read from the environment or the `.env` file only. Nothing is
hard-coded, and no key is ever sent to the frontend.

## The Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Quick check that the server is running |
| POST | `/api/trips` | Create a trip and generate an itinerary |
| GET | `/api/trips/{trip_id}` | Retrieve a saved trip |
| POST | `/api/trips/{trip_id}/modify` | Modify the itinerary from a message |
| POST | `/api/trips/{trip_id}/budget` | Calculate or recalculate the budget |
| GET | `/api/trips/{trip_id}/map` | The map of every day of the trip |
| POST | `/api/flights/search` | Search flights |
| POST | `/api/flights/booking-link` | A verified flight booking URL |
| POST | `/api/hotels/search` | Search hotels |
| POST | `/api/hotels/booking-link` | A verified hotel booking URL |
| POST | `/api/transport/search` | Search buses or trains |
| GET | `/api/weather` | Weather for a place and date |
| GET | `/api/maps/geocode` | Look up a place on the map |

Every error, whether it is a validation error, a 404 or a crash, comes back in
the same format:

```json
{ "error": { "code": "invalid_input", "message": "Destination is required." } }
```

## Search Filters

The three search endpoints take a `concession` and a `filters` object.

`concession` is one of `senior_citizen`, `army`, `student`, `doctor`, `nurse`,
or null.

`filters` is optional, and every field in it is optional too. A field left at
its default never removes a result.

| Field | Type | Notes |
| --- | --- | --- |
| `ac` | string | `any`, `ac`, `non_ac`. Buses and trains only. |
| `seat_class` | string | `any`, `seater`, `sleeper`. Buses and trains only. |
| `tracking` | boolean | Only services that can be tracked live |
| `is_new` | boolean | Only new vehicles |
| `price_min`, `price_max` | number | A price range |
| `departure_window` | string | `any`, `night`, `morning`, `afternoon`, `evening` |
| `sort` | string | `recommended`, `price_asc`, `price_desc`, `departure_asc`, `departure_desc`, `duration_asc`, `name_asc` |

The rules live in [`app/services/filters.py`](app/services/filters.py):

- A result that does not list its concessions is kept for every concession,
  because the provider did not say it was excluded.
- A result with no price is never removed by the price range.
- A result with no time is never removed by the departure window.
- A vehicle type that does not mention AC is kept under both the AC and the
  non-AC filter. Only a type that says "Non-AC" is excluded by the AC filter.
- Sorting changes the order of the results, never which results are returned.

The frontend applies the same rules to the results it gets back
(`frontend/src/utils/resultFilters.js`), so a filter takes effect straight
away and the sample data behaves the same way. The two must agree, and
[`tests/test_filters.py`](tests/test_filters.py) covers the backend side.

### Results

The results carry the fields the filters work on:

- `concessions`: the concessions the provider offers on that fare
- `tracking`: whether a bus or train can be tracked live
- `is_new`: whether a bus or train is a new vehicle
- `check_in_time`: when a hotel room can be checked into

## Project Structure

```
backend/
├── app/
│   ├── main.py            The FastAPI app and the CORS setup
│   ├── config.py          Every environment variable, read in one place
│   ├── errors.py          The one error format
│   ├── models/
│   │   ├── search.py      The request, filter and result models
│   │   ├── trip.py        The trip model
│   │   ├── maps.py        The map and route models
│   │   └── common.py      Shared validation
│   ├── routes/
│   │   ├── trips.py  flights.py  hotels.py  transport.py
│   │   └── maps.py   weather.py
│   ├── services/
│   │   ├── budget.py      The deterministic cost formulas
│   │   ├── filters.py     The search filters and sorting
│   │   ├── flights.py  hotels.py  transport.py
│   │   └── maps.py        Geocoding and routing
│   ├── ai/
│   │   ├── coordinator.py The AI conversation
│   │   ├── llm.py         The provider calls
│   │   ├── prompts.py     The prompts
│   │   └── tools.py       The tools the model can call
│   └── store.py  database.py  validators/
├── tests/                 The pytest suite
├── docs/                  api-testing, demo-prep, deployment, integration-tests
├── scripts/               check_backend.py and smoke_test.py
├── check.ps1              One command that checks the whole backend
└── requirements.txt
```

The routes are thin. They validate the request and hand it to a service. The
AI tools call the same services, so the model and the search pages get the same
answers.

## Recent Updates (October 2024)

✅ **Speed Optimization** - Reduced LLM timeout from 45s to 15s for faster responses  
✅ **Real Travel Data** - Integrated real carrier names (Air India, IndiGo, KSRTC, etc.)  
✅ **Live Data Sources** - Ready for Amadeus (flights) and Tavily (hotels) APIs  
✅ **Enhanced Budget UI** - Itemized breakdown with source attribution  
✅ **OpenStreetMap** - Free map tiles, no API key required  

See [REFACTOR_SUMMARY.md](../REFACTOR_SUMMARY.md) for complete details.

## Development Notes

- The backend uses sample data when no LLM provider is configured
- All API keys are loaded from environment variables only
- Error responses follow a consistent format: `{"error": {"code": "...", "message": "..."}}`
- Nothing is invented. When a place cannot be found, or a provider is not
  configured, the answer says so instead of making up coordinates or weather
- Booking links only point at verified providers, and only over `https`
- Real carrier/hotel names used in fallback data for realistic development
- The API contract is defined in [`../docs/api-contract.md`](../docs/api-contract.md)
- System architecture is documented in [`../docs/architecture.md`](../docs/architecture.md)

## Testing

Run the test suite:
```bash
pytest
```

The tests run against the app in-process, so no server needs to be running, and
they write to a throwaway database file.

To check the whole backend, including a live server and a smoke test:
```bash
.\check.ps1              # checks the server on http://127.0.0.1:8000
.\check.ps1 -Offline     # skips the live server checks
```

## Deployment

See the project README for deployment instructions.
