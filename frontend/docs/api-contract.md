# TriPlan API contract (draft v0)

Status: DRAFT. Frontend proposes this shape. Member 2 (backend) and Member 3 (AI) must
confirm or change it before integration. Update this file whenever a field changes.

## POST /api/trips

Creates a trip and returns the generated itinerary.

### Request

```json
{
  "origin": "Bengaluru",
  "destination": "Coorg",
  "days": 3,
  "budget": 15000,
  "people": 2,
  "travel_date": "2026-11-20",
  "interests": ["nature", "food", "adventure"],
  "diet": "vegetarian"
}
```

`origin` is optional and is left out when the user does not enter it.

### Success response (200)

The frontend sample in `frontend/src/services/mockTrip.js` is the reference shape.

| Field | Type | Notes |
| --- | --- | --- |
| trip_id | string | Used in the route /trips/:tripId |
| origin | string | Optional. Echo of the request. Used to fill in the booking pages. |
| destination | string | |
| travel_date | string | YYYY-MM-DD. Echo of the request. Used to fill in the booking pages. |
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

## POST /api/trips/{trip_id}/modify

Asks the assistant to change a plan. The response is a PROPOSED plan. The frontend shows
what would change and only replaces the current plan when the user chooses Apply.

Request:

```json
{ "message": "Make this trip cheaper", "current_trip": { "...": "the full current trip" } }
```

`current_trip` is sent so the backend does not need to have saved the trip. The backend
may ignore it if it stores trips.

Success response (200):

```json
{ "reply": "I removed one activity to lower the cost.", "trip": { "...": "full trip, same shape as above" } }
```

## POST /api/flights/search

Request: `{ "origin": "Bengaluru", "destination": "Goa", "date": "2026-11-20", "passengers": 2 }`

The search pages also send a `concession` and a `filters` object. See "Search filters" below.

Response: `{ "results": [ ... ] }`. Each result:

| Field | Type | Notes |
| --- | --- | --- |
| id | string | Unique within the response |
| airline | string | |
| departure_time, arrival_time | string | Shown as received, for example "06:30" |
| duration | string | For example "2h 15m" |
| stops | number | 0 means non-stop |
| price | number | Per person |
| currency | string | For example "INR" |
| booking_url | string or null | Must be an https URL. Anything else is ignored. |
| concessions | array of string | The concessions the provider offers on this fare. May be empty. |

An empty `results` array is a valid answer (the page shows "No flights found").

## POST /api/transport/search

Buses and trains. Request:
`{ "mode": "bus", "origin": "Bengaluru", "destination": "Madikeri", "date": "2026-11-20", "passengers": 2 }`
where `mode` is `bus` or `train`.

Response: `{ "results": [ ... ] }`. Each result: `id`, `operator`, `vehicle_type` (optional, for
example "AC sleeper"), `departure_time`, `arrival_time`, `duration`, `price` (per person),
`currency`, `booking_url` (https URL or null), `tracking` (boolean), `is_new` (boolean),
`concessions` (array of string).

## POST /api/hotels/search

Request: `{ "destination": "Goa", "check_in": "2026-11-20", "check_out": "2026-11-23", "guests": 2 }`

Response: `{ "results": [ ... ] }`. Each result: `id`, `name`, `area` (optional),
`price_per_night` (number), `currency`, `booking_url` (https URL or null),
`check_in_time` (optional "HH:MM"), `concessions` (array of string).

## Search filters

Every search page sends a `concession` and a `filters` object with the search.

`concession` is one of `senior_citizen`, `army`, `student`, `doctor`, `nurse`, or null.

`filters` is an object. Every field is optional, and a field left out never removes a result.

| Field | Type | Notes |
| --- | --- | --- |
| ac | string | `any`, `ac`, `non_ac`. Buses and trains only. |
| seat_class | string | `any`, `seater`, `sleeper`. Buses and trains only. |
| tracking | boolean | Only services that can be tracked live. Buses and trains only. |
| is_new | boolean | Only new vehicles. Buses and trains only. |
| price_min, price_max | number | A price range. A result with no price is never removed by it. |
| departure_window | string | `any`, `night`, `morning`, `afternoon`, `evening`. |
| sort | string | `recommended`, `price_asc`, `price_desc`, `departure_asc`, `departure_desc`, `duration_asc`, `name_asc` |

For hotels, the `departure_window` filter is applied to the check-in time.

The frontend also applies these filters to the results it gets back, so a filter takes effect
straight away and the page behaves the same on the built-in sample data.

## Notes for all endpoints

- Allowed values for `diet` in the trip request: `none`, `vegetarian`, `vegan`, `non-vegetarian`.
- `estimated_costs` may also include an optional `flights` number.
- The backend must allow requests from the frontend origin (CORS).
- Sample responses set `"is_mock": true`. The frontend labels these as sample data.

## Open questions

- Exact error codes.
- Whether the backend or the AI service owns the cost breakdown.
- Other endpoints from the project plan (modify, budget, route, flights, hotels) to be added
  as they are agreed.