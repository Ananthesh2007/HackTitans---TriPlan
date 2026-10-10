# TriPlan API contract (draft v0)

Status: DRAFT. Frontend proposes this shape. Member 2 (backend) and Member 3 (AI) must
confirm or change it before integration. Update this file whenever a field changes.

## POST /api/trips

Creates a trip and returns the generated itinerary.

### Request

```json
{
  "destination": "Coorg",
  "days": 3,
  "budget": 15000,
  "people": 2,
  "travel_date": "2026-11-20",
  "interests": ["nature", "food", "adventure"],
  "diet": "vegetarian"
}
```

### Success response (200)

The frontend sample in `frontend/src/services/mockTrip.js` is the reference shape.

| Field | Type | Notes |
| --- | --- | --- |
| trip_id | string | Used in the route /trips/:tripId |
| destination | string | |
| days | number | |
| people | number | |
| budget | number | The user's budget |
| currency | string | For example "INR" |
| is_estimate | boolean | Always true for AI-generated costs |
| estimated_costs | object | accommodation, food, activities, local_transport, total |
| itinerary | array | One item per day: day, title, activities |
| activities[] | array | time, name, location, estimated_cost |

### Error response (4xx or 5xx)

```json
{ "error": { "code": "invalid_input", "message": "Destination is required." } }
```

## Open questions

- Exact error codes.
- Whether the backend or the AI service owns the cost breakdown.
- Other endpoints from the project plan (modify, budget, route, flights, hotels) to be added
  as they are agreed.