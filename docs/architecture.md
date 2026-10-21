# TriPlan System Architecture

## Overview
TriPlan is a three-layer web application:
1. **Frontend**: React.js + Vite (SPA)
2. **Backend**: FastAPI (Python 3.11) 
3. **Services**: AI coordinator, budget calculator, external API wrappers

## Component Diagram

```
User Browser
    ↓ HTTP/JSON
React Frontend (Vite dev server)
    ↓ HTTP/JSON (CORS-enabled)
FastAPI Backend (Uvicorn workers)
    ├── Routes layer (validation, error handling)
    ├── Services layer (business logic)
    │   ├── AI Coordinator (LLM orchestration)
    │   ├── Budget Service (deterministic calculations)
    │   ├── Flights/Hotels/Transport (provider wrappers)
    │   └── Store (in-memory trip storage)
    └── External Services
        ├── LLM Provider (OpenAI/Gemini API)
        ├── Flight Search (Skyscanner, etc.)
        └── Hotel Search (Booking.com, etc.)
```

## Data Flow

### Trip Creation
1. User submits trip form → React validates client-side
2. React sends `POST /api/trips` with JSON body
3. FastAPI validates request with Pydantic (`TripRequest`)
4. Routes layer calls `app.ai.coordinator.generate_itinerary()`
5. AI Coordinator:
   - If LLM configured: calls `app.ai.llm.ask_for_json()`
   - On failure/fallback: uses `generate_mock_itinerary()`
6. Itinerary returned → Budget calculated by `app.services.budget.estimate_budget()`
7. Trip stored in-memory (`app.store.TRIPS`)
8. Returns `Trip` JSON to frontend

### Itinerary Modification
1. User types request → React sends `POST /api/trips/{id}/modify`
2. Backend validates, loads trip from store
3. Calls `app.ai.coordinator.modify_itinerary()`
4. Returns proposed `ModifyResponse` (reply + trip)
5. User reviews in frontend → confirms or cancels
6. If confirmed: frontend replaces current trip with proposed

### Search Flows (Flights/Hotels/Transport)
1. User submits search form → React validation
2. React sends `POST /api/{flights|hotels|transport}/search`
3. Backend validates, calls service layer
4. Service returns mock data (or live when provider configured)
5. Results shown in React cards/components
6. User clicks "Book Now" → gets verified URL via booking-link endpoint

## Key Technical Decisions

### State Management
- **Backend**: SQLite database persistence (`app/database.py`)
  - Date: 20-10-2026 — Migrated from in-memory to SQLite
  - Trips persist across server restarts
  - File-based storage: `backend/data/trips.db`
  - In-memory cache (TRIPS dict) maintained for backwards compatibility
  - Graceful fallback if database fails
  - Can be migrated to PostgreSQL for production scale
- **Frontend**: React state (useState, useContext)
  - Form state, trip state, UI state all client-side

### Error Handling
- Backend returns consistent JSON error format:
  ```json
  {"error": {"code": "snake_case", "message": "Safe user message"}}
  ```
- Never exposes stack traces or internal details
- AI failures fall back gracefully to mock data

### Security
- API keys stored in environment variables only (never in code)
- `.env` listed in `.gitignore`
- `.env.example` shows required variables without secrets
- CORS restricted to known frontend origins
- Input validation via Pydantic at API boundary

### External Integrations
- All external calls wrapped in service-layer functions
- Failures return clear messages, never crash
- Booking links go to verified providers only (allowlisted)
- No payment or personal data collected by TriPlan

## Directory Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app creation + middleware
│   ├── config.py            # Environment variable loading
│   ├── errors.py            # Standard error format
│   │
│   ├── ai/                  # Member 3 responsibility
│   │   ├── coordinator.py   # Orchestrates LLM + validation
│   │   ├── llm.py           # HTTP client + retry + JSON extraction
│   │   └── prompts.py       # Prompt templates + JSON schemas
│   │
│   ├── services/            # Business logic layer
│   │   ├── budget.py        # Deterministic cost calculations
│   │   ├── flights.py       # Mock/live flight search wrappers
│   │   ├── hotels.py        # Mock/live hotel search wrappers
│   │   └── maps.py          # Geocoding + route planning
│   │
│   ├── models/              # Pydantic models (DTOs)
│   │   ├── trip.py          # Trip, DayPlan, Activity, etc.
│   │   ├── search.py        # Flight/Hotel/Transport search shapes
│   │   └── maps.py          # Coordinates, stops, route shapes
│   │
│   ├── routes/              # FastAPI routers (HTTP endpoints)
│   │   ├── trips.py         # POST/GET /api/trips*
│   │   ├── flights.py       # POST /api/flights/*
│   │   ├── hotels.py        # POST /api/hotels/*
│   │   ├── transport.py     # POST /api/transport/*
│   │   ├── weather.py       # GET /api/weather
│   │   └── maps.py          # GET /api/maps/*, GET /api/trips/{id}/map
│   │
│   └── store.py             # In-memory trip storage (dict)
│
├── requirements.txt         # Python dependencies
├── .env.example            # Template for developers
└── .gitignore              # Keeps secrets out of repo
```

## Contract Enforcement
- API contract lives in `docs/api-contract.md` (source of truth)
- Frontend and backend both implement the same JSON shapes
- Changes require updating the contract document first
- During development: mock data matches contract exactly
- In production: live provider data must conform to same shapes

## Scaling Considerations
- Stateless backend (except in-memory trip store)
- Horizontal scaling possible with shared trip store (Redis/DB)
- AI calls are latency-sensitive; timeout configured at 45s
- Budget service is pure deterministic math (instantaneous)