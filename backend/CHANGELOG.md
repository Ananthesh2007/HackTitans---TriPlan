# TriPlan Backend Changelog

This document tracks all changes made during Sprint 4 (Oct 20-25, 2026) as per the timetable in back.md.

## 2026-10-20 (Tuesday) - Database Persistence Implementation

### Added
- **SQLite database persistence** (`app/database.py`)
  - Created `TripDatabase` class with full CRUD operations
  - Implements proper error handling - never reports success if database fails
  - Automatic JSON serialization/deserialization for trip data
  - Date object handling for travel_date field
  - Database file location: `backend/data/trips.db`

### Modified
- **Trip storage module** (`app/store.py`)
  - Migrated from pure in-memory storage to database-backed persistence
  - Added `save_trip()`, `get_trip()`, `delete_trip()` functions with error handling
  - Maintains in-memory cache (TRIPS dict) for backwards compatibility
  - Lazy database initialization to avoid import delays
  - Returns False if database save fails (never lies about persistence)

- **Trip routes** (`app/routes/trips.py`)
  - Updated `create_trip()` to save to database with error handling
  - Modified `get_trip()` to read from database first, then fallback to cache
  - Updated `modify_trip()` to persist changes to database
  - Modified `calculate_budget()` to use database storage
  - Added warning message when trip cannot be persisted

### Status
✅ **COMPLETED** - Database persistence implemented with proper error handling as per timetable requirement: "never report a trip as saved if the database fails"

---

## 2026-10-21 (Wednesday) - Optional Weather Feature

### Added
- **Weather endpoint** (`app/routes/weather.py`)
  - GET `/api/weather` endpoint for weather information
  - Accepts `city` query parameter
  - Returns mock weather data (placeholder for real provider integration)
  - Includes current conditions and 3-day forecast
  - Safe error handling - never fabricates data

- **Weather router registration** (`app/main.py`)
  - Added weather router to FastAPI app
  - Marked as optional feature (defer if provider unavailable)

### Status
✅ **COMPLETED** - Optional weather feature added as placeholder. Real provider integration deferred pending API access.

---

## 2026-10-22 (Thursday) - Integration Testing

### Planned Tests
- [ ] Invalid AI output handling
- [ ] Provider down scenarios (flights, hotels, weather)
- [ ] Database failure scenarios
- [ ] External booking link failures
- [ ] Network timeout handling
- [ ] Malformed request validation
- [ ] Large payload handling

### Expected Outcome
All error scenarios return clear JSON and nothing crashes. Every endpoint returns consistent error format.

### Status
🔄 **PENDING** - Scheduled for Oct 22, 2026

---

## 2026-10-23 (Friday) - Backend Deployment

### Deployment Checklist
- [ ] Deploy backend on Render (or equivalent host)
- [ ] Set environment variables (.env configuration)
- [ ] Restrict CORS to live domain only
- [ ] Confirm HTTPS is enabled
- [ ] Point frontend at live API URL
- [ ] Test health endpoint
- [ ] Verify database persistence on server

### Configuration Requirements
- `FRONTEND_ORIGINS` - Set to live frontend URL
- `LLM_PROVIDER` - OpenAI or Gemini
- `LLM_API_KEY` - AI provider API key
- `LLM_MODEL` - Model name (e.g., gpt-4o-mini)
- `APP_ENV` - Set to "production"

### Status
🔄 **PENDING** - Scheduled for Oct 23, 2026

---

## 2026-10-24 (Saturday) - Final Testing

### Test Checklist
- [ ] Test all endpoints with live API
- [ ] Verify database persistence works on production
- [ ] Test trip creation end-to-end
- [ ] Test trip modification with real AI
- [ ] Verify budget calculations
- [ ] Test flights/hotels search endpoints
- [ ] Test error handling in production
- [ ] Check backend items on launch checklist
- [ ] Fix critical issues only

### Status
🔄 **PENDING** - Scheduled for Oct 24, 2026

---

## 2026-10-25 (Sunday) - Demo Preparation

### Buffer Day Tasks
- [ ] Write `docs/architecture.md` (update with database changes)
- [ ] Support demo script preparation
- [ ] Keep working fallback for demo day
- [ ] Freeze backend code (no more changes)
- [ ] Document any known limitations
- [ ] Prepare fallback scenarios for demo

### Status
🔄 **PENDING** - Scheduled for Oct 25, 2026

---

## Technical Notes

### Database Implementation Details
The SQLite database provides:
- File-based persistence (no external database server needed)
- Simple migration path to PostgreSQL later
- Thread-safe operations
- Automatic table creation on startup
- JSON storage for flexible schema evolution

### Error Handling Strategy
All database operations follow the pattern:
1. Try database operation first
2. Log errors but never crash
3. Fall back to in-memory cache if needed
4. Return clear boolean/None to indicate failure
5. Never report success if persistence failed

### Backwards Compatibility
The in-memory TRIPS dict is maintained during transition:
- New code uses database functions
- Old code accessing TRIPS dict still works
- Cache automatically syncs with database
- Will be fully removed in future sprint

---

## Files Modified

### Created
- `backend/app/database.py` - SQLite database module
- `backend/app/routes/weather.py` - Weather endpoint
- `backend/CHANGELOG.md` - This file

### Modified
- `backend/app/store.py` - Database-backed storage
- `backend/app/routes/trips.py` - Database persistence in routes
- `backend/app/main.py` - Added weather router

### To Be Modified (Oct 22+)
- `backend/docs/architecture.md` - Update with database info
- `backend/README.md` - Deployment instructions
- Test files (to be created for integration tests)
