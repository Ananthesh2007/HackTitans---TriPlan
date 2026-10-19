# TriPlan Backend Timetable

10 to 25 October 2026. Sprint 1, the Learning Sprint (Oct 3 to 9), comes before this timetable.

## Sprint 2: Dev Sprint (Oct 10 to 16)

| **Date** | **Task** | **End-of-day deliverable** |
| --- | --- | --- |
| **Sat 10 Oct** | Create the FastAPI app in backend/ with the folder structure from the plan. Add a health route, CORS for the frontend, requirements.txt, and .env.example. Agree the API contract with Members 1 and 3 and write docs/api-contract.md. Return mock data that matches the contract. | Server runs, contract written |
| **Sun 11** | Build POST /api/trips with Pydantic validation for destination, days, budget, people, travel_date, interests, and diet. Return one consistent JSON error format. Respond with a mock itinerary for now. | Validated endpoint |
| **Mon 12** | Turn Member 3’s itinerary schema into models in models/. Write validate_plan() to check structure. Add GET /api/trips/{trip_id} backed by an in-memory store. | Trip endpoints on mock data |
| **Tue 13** | Call Member 3’s generate_itinerary() from POST /api/trips. Handle LLM failures and invalid JSON without crashing. Keep API keys in environment variables only. | Real itinerary from the API |
| **Wed 14** | Write estimate_budget() in services/budget.py using deterministic code, and add POST /api/trips/{trip_id}/budget. Label every figure as an estimate and flag when the budget is below the estimate. | Budget endpoint |
| **Thu 15** | Add POST /api/trips/{trip_id}/modify using Member 3’s modify_itinerary(). Validate the revised plan, recalculate the budget, and return the result for the user to review. | Chat changes a trip |
| **Fri 16** | Add POST /api/flights/search, /api/hotels/search, and the two booking-link endpoints with an allowlist of verified URLs. Return a clear “provider unavailable” response with an external search option. Start investigating live-data providers. | Search and redirect endpoints |

## Sprint 3: Review Sprint (Oct 17 to 18)

| **Date** | **Task** | **End-of-day deliverable** |
| --- | --- | --- |
| **Sat 17 Oct** | No new features. Test every endpoint against the plan’s test table, check integration with the real frontend, and review as a team. | Prioritised bug list |
| **Sun 18** | Fix critical bugs. Choose the database (PostgreSQL or Firebase) or defer it, and set up the hosting account for deployment. Pick the Sprint 4 priorities. | Clean build, hosting ready |

## Sprint 4: Final Dev Sprint (Oct 19 to 25)

| **Date** | **Task** | **End-of-day deliverable** |
| --- | --- | --- |
| **Mon 19 Oct** | Fix remaining review bugs. Check that no secrets are in the repository, add input limits, and confirm external URLs are validated. | Bugs fixed, secrets safe |
| **Tue 20** | Add saved trips only if the database is in scope: save and retrieve trips, and never report a trip as saved if the database fails. Otherwise document the decision to defer. | Persistence in or deferred |
| **Wed 21** | Add get_weather() with GET /api/weather and the route endpoint only if provider access is available. Never return a fabricated forecast. Otherwise skip. | Optional features in or deferred |
| **Thu 22** | Full integration test: invalid AI output, provider down, database failure, and external booking failure. Confirm every error returns clear JSON and nothing crashes. | Stable build |
| **Fri 23** | Deploy the backend on Render or an equivalent host. Set the environment variables, restrict CORS to the live domain, confirm HTTPS, and point the frontend at the live API. | Live API |
| **Sat 24** | Final test of the live API with the live site. Check the backend items on the launch checklist. Fix critical issues only. | Backend checks ticked |
| **Sun 25** | Buffer day. Write docs/architecture.md, support the demo script, and keep a working fallback for demo day. Backend frozen. | Demo-ready |