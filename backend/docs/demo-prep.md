# Demo Preparation Guide (Oct 25, 2026)

Buffer day tasks for demo readiness. Backend is frozen - no new features.

## Demo Day Checklist

### 1. Documentation Complete
- [x] `docs/architecture.md` updated with database info
- [ ] `docs/api-contract.md` verified against implementation
- [ ] `backend/README.md` with deployment instructions
- [ ] `backend/CHANGELOG.md` complete for Sprint 4

### 2. Fallback Scenarios Ready

#### AI Provider Failure
If LLM is slow/down during demo:
```bash
# Set in Render environment variables:
FORCE_MOCK_AI=true
```
Result: Uses built-in mock itinerary, demo continues smoothly

#### Database Failure
If database has issues:
- Fallback to in-memory cache automatically
- Warning message shown in response
- Demo continues with warning

#### External Provider Down
If flights/hotels search fails:
- Returns mock data with `is_mock: true`
- Shows "provider unavailable" with alternative
- Demo continues

#### Network Timeout
If requests timeout:
- Set `LLM_TIMEOUT_SECONDS=30` for faster demo
- 45s default may feel slow in demo

### 3. Demo Script Support

#### Sample Demo Flow
```
1. Health Check: GET /health
   → Show service is running

2. Create Trip: POST /api/trips
   → Origin: "Mumbai"
   → Destination: "Goa"
   → Days: 3
   → Budget: ₹20,000
   → People: 2
   → Show generated itinerary

3. Retrieve Trip: GET /api/trips/{trip_id}
   → Prove persistence works

4. Modify Trip: POST /api/trips/{trip_id}/modify
   → Message: "Add a beach visit on day 2"
   → Show updated itinerary

5. Budget Check: POST /api/trips/{trip_id}/budget
   → Show cost breakdown

6. Search Flights: POST /api/flights/search
   → Show mock flight results

7. Search Hotels: POST /api/hotels/search
   → Show mock hotel results

8. Weather: GET /api/weather?place=Goa&date=2026-11-20
   → Show weather info
```

#### Demo Data (Pre-seeded)
Consider creating a few test trips beforehand:
- Short weekend trip (2 days, ₹10,000)
- Week-long vacation (7 days, ₹50,000)
- Budget trip (3 days, ₹5,000)
Show variety in the demo

### 4. Known Limitations

Document these for judges:
1. **Mock Data**: Flights/hotels use mock data (no live provider API yet)
2. **Weather**: Mock weather data (no real weather API)
3. **Booking**: Redirects to external sites (no in-app booking)
4. **Database**: SQLite (not suitable for high scale production)
5. **AI**: Costs are estimates only

### 5. Backend Frozen

**No more code changes after Oct 25.**

Allowed changes ONLY if critical bug found:
- Typos in error messages
- Security fixes
- Configuration adjustments

NOT allowed:
- New features
- API changes
- Database schema changes
- Refactoring

### 6. Architecture Documentation

Update `docs/architecture.md` with:
- [x] Database section (SQLite implementation)
- [ ] Deployment details (Render hosting)
- [ ] Environment variables reference
- [ ] API endpoints summary
- [ ] Error handling flow
- [ ] Security measures

### 7. Performance Metrics

Have these ready for Q&A:
- Average response time: ___ ms
- Database query time: ___ ms
- AI generation time: ___ s
- Memory usage: ___ MB

### 8. Backup Plans

#### If Backend Crashes
1. Check Render logs immediately
2. Restart service from Render dashboard
3. Have local backup running: `uvicorn app.main:app --reload`
4. Switch frontend to local backend URL

#### If Database Corrupt
1. Delete `trips.db` file
2. Backend will recreate automatically
3. Demo with fresh data

#### If Everything Fails
1. Use mock mode: `FORCE_MOCK_AI=true`
2. Focus on frontend UI/UX
3. Explain the architecture verbally
4. Show pre-recorded demo video (if available)

## Post-Demo Tasks

After demo day:
- [ ] Gather feedback from judges
- [ ] Document questions asked
- [ ] Note areas for improvement
- [ ] Archive Sprint 4 work
- [ ] Plan Sprint 5 (if project continues)

## Date: 25-10-2026 - Buffer day, demo preparation
Status: Pending - Complete documentation, prepare fallbacks, freeze backend.

## Quick Reference

**Production API**: `https://triplan-backend.onrender.com`
**Health Check**: `https://triplan-backend.onrender.com/health`
**API Docs**: `https://triplan-backend.onrender.com/docs`

**Fallback Local**: `http://localhost:8000`
**Mock Mode**: `FORCE_MOCK_AI=true`
