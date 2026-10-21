# TriPlan API Contract

Agreed upon by all team members on 10 Oct 2026.
This document describes the exact JSON shape of every request and response.
All timestamps are in ISO 8601 UTC. All money amounts are in INR (Indian Rupees).

## Common Definitions

- **Place**: A non-empty string (2-80 chars) after trimming whitespace.
- **Interest**: One of `"nature" | "food" | "adventure" | "culture" | "history" | "beaches" | "relaxation" | "shopping"`.
- **Diet**: One of `"none" | "vegetarian" | "vegan" | "non-vegetarian"`.
- **Concession**: One of `"senior_citizen" | "army" | "student" | "doctor" | "nurse"`. The category the
  traveller books under. A traveller picks at most one.
- **Filters**: The filters a search page sends with the search. Every field is optional, and a
  field left out never removes a result.

### Filters object

```json
{
  "ac": "any",
  "seat_class": "any",
  "tracking": false,
  "is_new": false,
  "price_min": null,
  "price_max": null,
  "departure_window": "any",
  "sort": "recommended"
}
```
- `ac`: `"any" | "ac" | "non_ac"` (buses and trains)
- `seat_class`: `"any" | "seater" | "sleeper"` (buses and trains)
- `tracking`: boolean – only services that can be tracked live
- `is_new`: boolean – only new vehicles
- `price_min`, `price_max`: number ≥ 0 or null
- `departure_window`: `"any" | "night" | "morning" | "afternoon" | "evening"`
  (night 00:00-06:00, morning 06:00-12:00, afternoon 12:00-18:00, evening 18:00-24:00)
- `sort`: `"recommended" | "price_asc" | "price_desc" | "departure_asc" | "departure_desc" | "duration_asc" | "name_asc"`

### How the filters are applied

- A filter left at its default never removes a result.
- A result that does not list its concessions is kept for every concession, because the provider
  did not say it was excluded. A result that does list them is kept only for the concessions it
  lists.
- A result with no price is never removed by the price range.
- A result with no time is never removed by the departure window.
- Sorting changes the order of the results, never which results are returned.

## POST /api/trips
Create a trip and generate an itinerary.

### Request
```json
{
  "origin": "Mangalore",
  "destination": "Coorg",
  "days": 3,
  "budget": 15000,
  "people": 2,
  "travel_date": "2026-11-20",
  "interests": ["nature", "food", "adventure"],
  "diet": "vegetarian"
}
```
- `origin`: Place (optional)
- `destination`: Place (required)
- `days`: integer, 1-30 (required)
- `budget`: number > 0 (required)
- `people`: integer, 1-20 (required)
- `travel_date`: ISO 8601 date (required, must be today or later)
- `interests`: array of Interest (optional, max 8)
- `diet`: Diet (optional, default `"none"`)

### Response (200)
```json
{
  "trip_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "is_mock": false,
  "is_estimate": true,
  "origin": "Mangalore",
  "destination": "Coorg",
  "travel_date": "2026-11-20",
  "days": 3,
  "people": 2,
  "budget": 15000,
  "currency": "INR",
  "estimated_costs": {
    "flights": 9600,
    "accommodation": 12000,
    "food": 6000,
    "activities": 3640,
    "local_transport": 3000,
    "total": 34240
  },
  "itinerary": [
    {
      "day": 1,
      "title": "Day 1 in Coorg",
      "activities": [
        {
          "time": "09:00",
          "name": "Local sightseeing tour",
          "location": "City centre, Coorg",
          "estimated_cost": 100
        },
        {
          "time": "11:00",
          "name": "Nature walk",
          "location": "National park, Coorg",
          "estimated_cost": 300
        },
        {
          "time": "14:00",
          "name": "Cultural museum visit",
          "location": "Old town, Coorg",
          "estimated_cost": 200
        }
      ]
    },
    {
      "day": 2,
      "title": "Day 2 in Coorg",
      "activities": [
        {
          "time": "11:00",
          "name": "Nature walk",
          "location": "National park, Coorg",
          "estimated_cost": 300
        },
        {
          "time": "14:00",
          "name": "Cultural museum visit",
          "location": "Old town, Coorg",
          "estimated_cost": 200
        },
        {
          "time": "16:00",
          "name": "Traditional food experience",
          "location": "Local market, Coorg",
          "estimated_cost": 150
        }
      ]
    },
    {
      "day": 3,
      "title": "Day 3 in Coorg",
      "activities": [
        {
          "time": "11:00",
          "name": "Nature walk",
          "location": "National park, Coorg",
          "estimated_cost": 300
        },
        {
          "time": "16:00",
          "name": "Traditional food experience",
          "location": "Local market, Coorg",
          "estimated_cost": 150
        },
        {
          "time": "18:30",
          "name": "Riverside stroll",
          "location": "Waterfront, Coorg",
          "estimated_cost": 120
        }
      ]
    }
  ],
  "warning": null,
  "reply": null
}
```
- `trip_id`: UUID v4 string
- `is_mock`: boolean – true when the AI provider was not used
- `is_estimate`: boolean – always true (all costs are estimates)
- `origin`, `destination`, `travel_date`, `days`, `people`, `budget`, `currency`: echoed from request
- `estimated_costs`: deterministic breakdown (see `POST /api/trips/{trip_id}/budget`) — for the whole group, not per person
- `budget`: the user's own budget. It is compared against the estimate; it does not scale the estimate.
- `itinerary`: array of day objects (exactly `days` long)
  - `day`: integer, 1-based
  - `title`: non-empty string
  - `activities`: array of 3-5 activity objects
    - `time`: HH:MM 24-hour string
    - `name`: non-empty string
    - `location`: non-empty string
    - `estimated_cost`: number ≥ 0 (per-person, in INR)
- `warning`: string or null – explains when AI was unavailable
- `reply`: string or null – assistant's short reply (only on modification responses)

### Error Responses
- **422 Unprocessable Entity**: validation error on the request body
- **502 Bad Gateway**: AI returned malformed JSON or violated the schema
- **500 Internal Server Error**: unexpected error (never exposes internals)

## GET /api/trips/{trip_id}
Retrieve a trip by its ID.

### Response (200)
Same shape as the POST response.

### Error Responses
- **404 Not Found**: no trip with that ID

## POST /api/trips/{trip_id}/modify
Ask the assistant to revise the current itinerary.

### Request
```json
{
  "message": "Remove museums and add more adventure activities."
}
```
- `message`: non-empty string (max 500 chars)

### Response (200)
```json
{
  "reply": "Removed the cultural museum visit and added a nature trek on day 2.",
  "trip": {
    /* Same shape as a trip object from POST /api/trips */
  }
}
```
- `reply`: assistant's explanation of what changed
- `trip`: the proposed revised itinerary (user must confirm in frontend)

### Error Responses
- **404 Not Found**: trip not found
- **422 Unprocessable Entity**: the revised plan failed validation
- **502 Bad Gateway**: AI returned unusable output
- **500 Internal Server Error**: unexpected error

## POST /api/trips/{trip_id}/budget
Calculate or recalculate the budget for a trip.

### Response (200)
```json
{
  "trip_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "estimated_costs": {
    "flights": 9600,
    "accommodation": 12000,
    "food": 6000,
    "activities": 3640,
    "local_transport": 3000,
    "total": 34240
  },
  "budget_status": {
    "budget": 15000,
    "estimate": 34240,
    "is_below_estimate": true,
    "shortfall": 19240,
    "message": "Your estimated costs (₹34,240) exceed your budget (₹15,000). Consider adjusting your trip or increasing your budget."
  }
}
```
- `trip_id`: echoed
- `estimated_costs`: deterministic breakdown (flights, accommodation, etc.), for the whole group
  - `flights`: ₹4,800 per person
  - `accommodation`: ₹2,000 per person per night
  - `food`: ₹1,000 per person per day
  - `activities`: the sum of the plan's per-activity costs, multiplied by the number of people
  - `local_transport`: ₹500 per person per day
- `budget_status`:
  - `budget`: number from trip.budget
  - `estimate`: number from estimated_costs.total
  - `is_below_estimate`: true when budget < estimate
  - `shortfall`: estimate - budget (0 when not below)
  - `message`: explanation or null

## POST /api/flights/search
Search for flights.

### Request
```json
{
  "origin": "Mangalore",
  "destination": "New York",
  "date": "2026-11-20",
  "passengers": 1,
  "concession": "senior_citizen",
  "filters": { "price_max": 6000, "sort": "price_asc" }
}
```
- `origin`: Place (required)
- `destination`: Place (required, must differ from origin)
- `date`: ISO 8601 date (required, must be today or later)
- `passengers`: integer, 1-9 (required)
- `concession`: Concession or null (optional, default null)
- `filters`: Filters object (optional, default null)

### Response (200)
```json
{
  "is_mock": true,
  "results": [
    {
      "id": "flight-001",
      "airline": "Sample Airline A",
      "departure_time": "06:30",
      "arrival_time": "08:45",
      "duration": "2h 15m",
      "stops": 0,
      "price": 4800,
      "currency": "INR",
      "booking_url": null,
      "concessions": ["senior_citizen", "student", "army"]
    }
  ]
}
```
- `is_mock`: boolean – true when no live provider is integrated
- `results`: array of flight objects
  - `id`: string (unique within this response)
  - `airline`: string or null
  - `departure_time`: HH:MM string or null
  - `arrival_time`: HH:MM string or null
  - `duration`: string like `"2h 15m"` or null
  - `stops`: integer ≥ 0 or null
  - `price`: number ≥ 0 or null (per person)
  - `currency`: `"INR"` (fixed)
  - `booking_url`: string or null – when present, must start with `https://` and be from a verified provider
  - `concessions`: array of Concession the provider offers on this fare (may be empty)

## POST /api/flights/booking-link
Get a verified booking URL for a flight.

### Request
```json
{
  "flight_id": "flight-001"
}
```
- `flight_id`: string (must match an id from the last search response)

### Response (200)
```json
{
  "flight_id": "flight-001",
  "booking_url": "https://www.makemytrip.com/",
  "message": "Complete your booking on the external provider's website."
}
```
- `flight_id`: echoed
- `booking_url`: verified URL (see allowlist in code)
- `message`: user-facing explanation

## POST /api/hotels/search
Search for hotels.

### Request
```json
{
  "destination": "New York",
  "check_in": "2026-11-20",
  "check_out": "2026-11-23",
  "guests": 2,
  "rooms": 1,
  "concession": "senior_citizen",
  "filters": { "price_max": 3000 }
}
```
- `destination`: Place (required)
- `check_in`: ISO 8601 date (required, must be today or later)
- `check_out`: ISO 8601 date (required, must be after check_in)
- `guests`: integer, 1-20 (required)
- `rooms`: integer, 1-10 (optional, defaults to 1; implied by guests)
- `concession`: Concession or null (optional, default null)
- `filters`: Filters object (optional, default null)

### Response (200)
```json
{
  "is_mock": true,
  "results": [
    {
      "id": "hotel-001",
      "name": "Sample Hotel A",
      "area": "City centre",
      "price_per_night": 2200,
      "currency": "INR",
      "booking_url": null,
      "check_in_time": "14:00",
      "concessions": ["senior_citizen", "army", "student"]
    }
  ]
}
```
- `is_mock`: boolean – true when no live provider is integrated
- `results`: array of hotel objects
  - `id`: string (unique within this response)
  - `name`: string or null
  - `area`: string or null
  - `price_per_night`: number ≥ 0 or null
  - `currency`: `"INR"` (fixed)
  - `booking_url`: string or null – when present, must start with `https://` and be from a verified provider
  - `check_in_time`: HH:MM string or null – the time the room can be checked into
  - `concessions`: array of Concession the provider offers on this rate (may be empty)

## POST /api/hotels/booking-link
Get a verified booking URL for a hotel.

### Request
```json
{
  "hotel_id": "hotel-001"
}
```
- `hotel_id`: string (must match an id from the last search response)

### Response (200)
```json
{
  "hotel_id": "hotel-001",
  "booking_url": "https://www.booking.com/",
  "message": "Complete your booking on the external provider's website."
}
```
- `hotel_id`: echoed
- `booking_url`: verified URL (see allowlist in code)
- `message`: user-facing explanation

## POST /api/transport/search
Search for buses or trains.

### Request
```json
{
  "origin": "Mangalore",
  "destination": "Bangalore",
  "date": "2026-11-20",
  "passengers": 2,
  "mode": "train",
  "concession": "senior_citizen",
  "filters": { "ac": "ac", "seat_class": "sleeper", "tracking": true }
}
```
- `origin`: Place (required)
- `destination`: Place (required, must differ from origin)
- `date`: ISO 8601 date (required, must be today or later)
- `passengers`: integer, 1-9 (required)
- `mode`: `"bus"` or `"train"` (required)
- `concession`: Concession or null (optional, default null)
- `filters`: Filters object (optional, default null). The `ac`, `seat_class`, `tracking` and
  `is_new` filters apply to buses and trains.

### Response (200)
```json
{
  "is_mock": true,
  "results": [
    {
      "id": "train-001",
      "operator": "Sample Express 1",
      "vehicle_type": "Sleeper class",
      "departure_time": "20:10",
      "arrival_time": "06:00",
      "duration": "9h 50m",
      "price": 480,
      "currency": "INR",
      "booking_url": null,
      "tracking": true,
      "is_new": false,
      "concessions": ["senior_citizen", "student", "army"]
    }
  ]
}
```
- `is_mock`: boolean – true when no live provider is integrated
- `results`: array of transport objects
  - `id`: string (unique within this response)
  - `operator`: string or null
  - `vehicle_type`: string or null
  - `departure_time`: HH:MM string or null
  - `arrival_time`: HH:MM string or null
  - `duration`: string like `"9h 50m"` or null
  - `price`: number ≥ 0 or null (per person)
  - `currency`: `"INR"` (fixed)
  - `booking_url`: string or null – when present, must start with `https://` and be from a verified provider
  - `tracking`: boolean – true when the service can be tracked live
  - `is_new`: boolean – true when the vehicle is a new one
  - `concessions`: array of Concession the provider offers on this fare (may be empty)

## GET /api/weather
Get weather information for a place and date.

### Request (query parameters)
```
/api/weather?place=Coorg&date=2026-11-20
```
- `place`: Place (required)
- `date`: ISO 8601 date (required, must be today or later)

### Response (200) – when weather provider is available
```json
{
  "place": "Coorg",
  "date": "2026-11-20",
  "condition": "Partly cloudy",
  "temperature_min": 18,
  "temperature_max": 28,
  "humidity": 65,
  "description": "Light clouds with sunny intervals."
}
```
- `place`: echoed
- `date`: echoed
- `condition`: string (e.g. `"Sunny"`, `"Rain"`)
- `temperature_min`: integer (°C)
- `temperature_max`: integer (°C)
- `humidity`: integer (%) 
- `description`: string or null

### Response (200) – when provider is not available
```json
{
  "place": "Coorg",
  "date": "2026-11-20",
  "error": "Weather service not configured."
}
```
- `place`: echoed
- `date`: echoed
- `error`: explanation – never invents weather data

## GET /api/maps/geocode
Look up a place name and return where it is on the map.

### Request (query parameters)
```
/api/maps/geocode?place=Cubbon Park, Bengaluru
```
- `place`: Place (required)

### Response (200) – when the place is found
```json
{
  "place": "Cubbon Park, Bengaluru",
  "name": "Cubbon Park",
  "display_name": "Cubbon Park, Sampangirama Nagar, Bengaluru, Karnataka, India",
  "coordinates": { "lat": 12.9742535, "lng": 77.5921906 },
  "provider": "osm",
  "map_url": "https://www.openstreetmap.org/?q=12.9742535,77.5921906"
}
```
- `place`: echoed
- `coordinates`: latitude and longitude
- `provider`: `"osm"` or `"google"`
- `map_url`: a link that opens the point in a map

### Response (200) – when the place is not found
```json
{
  "place": "Cubbon Park, Bengaluru",
  "error": "This place could not be found on the map."
}
```
- Never returns invented coordinates.

### Response (200) – when no map provider is configured
```json
{
  "place": "Cubbon Park, Bengaluru",
  "error": "Map service not configured."
}
```

## GET /api/trips/{trip_id}/map
The map of every day of a trip.

### Response (200)
```json
{
  "trip_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "destination": "Coorg",
  "provider": "osm",
  "is_mock": false,
  "warning": null,
  "days": [
    {
      "day": 1,
      "title": "Day 1 in Coorg",
      "stops": [
        {
          "order": 1,
          "name": "Local sightseeing tour",
          "location": "City centre, Coorg",
          "coordinates": { "lat": 12.4244, "lng": 75.7382 },
          "map_url": "https://www.openstreetmap.org/?q=12.4244,75.7382(Local sightseeing tour)"
        }
      ],
      "route": {
        "provider": "osm",
        "mode": "driving",
        "distance_km": 7.94,
        "duration_minutes": 11.9,
        "points": [{ "lat": 12.9742, "lng": 77.5921 }],
        "legs": [
          {
            "from_stop": "Cubbon Park",
            "to_stop": "Palace",
            "distance_km": 2.81,
            "duration_minutes": 4.1
          }
        ],
        "is_estimate": false,
        "warning": null
      },
      "warning": null
    }
  ]
}
```
- `provider`: the maps provider that answered, or `null` when none is configured
- `is_mock`: true when no provider answered, so the map is empty
- `days[].stops[].coordinates`: `null` when the place could not be located
- `days[].route.points`: the line to draw on the map. Empty when the provider gave no geometry. The line is thinned to at most 120 points.
- `days[].route.is_estimate`: true when the distance is a straight-line calculation, not route data
- `days[].warning`: says how many places could not be located

### Error Responses
- **404 Not Found**: no trip with that ID

### Notes
- The provider is asked at most once a second, as the OpenStreetMap usage policy asks. Answers are cached for 24 hours, so opening the same trip again is instant.
- The first request for a trip can take a few seconds, because every place in the plan has to be looked up.

## Error Format
Every error response (4xx or 5xx) returns:
```json
{
  "error": {
    "code": "short_error_code",
    "message": "Human-readable explanation",
    "details": null   /* optional array or object */
  }
}
```
- `code`: snake_case, stable across versions
- `message`: safe to show the user
- `optional`: additional machine-readable details (never secrets)
