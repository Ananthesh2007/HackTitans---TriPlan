# TriPlan Frontend

The React interface for TriPlan: the trip planner, the trip dashboard, the AI
chat assistant, and the flight, bus/train and hotel search pages with their
filters.

The design system is called "TriPlan Dark" — a high-contrast, aviation-oriented
dark theme with bold Urbanist typography, white text, and a restrained red
accent. It lives in `src/index.css`.

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

To use the built-in sample data instead of calling the backend, set
`VITE_USE_MOCK=true` in `frontend/.env.local` (see `.env.example`).

```bash
npm run build     # build for production into dist/
npm run preview   # serve the production build locally
npm run lint      # ESLint
```

## Environment Variables

Copy `.env.example` to `.env.local` and fill in your own values. The
`.env.local` file must never be committed to Git.

| Variable | Default | What it does |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000` | The address of the TriPlan backend |
| `VITE_USE_MOCK` | `false` | `true` uses the built-in sample data instead of the backend |
| `VITE_MAP_TILE_URL` | dark CARTO tiles | A different tile server for the map |
| `VITE_MAP_TILE_ATTRIBUTION` | CARTO credit | The credit line shown on the map. Keep the provider's attribution |

No API key is ever put in the frontend. The backend holds the provider keys.

## The Pages

| Route | What it does |
| --- | --- |
| `/` | The home page |
| `/plan` | The trip form. Enter a destination, dates, travellers, budget, interests and food preference, and generate an itinerary. |
| `/trips/:tripId` | The dashboard: budget, map, day-by-day plan, booking links, and the AI chat assistant |
| `/flights` | Flight search, with filters |
| `/transport` | Bus and train search, with filters |
| `/hotels` | Hotel search, with filters |

The dashboard is reachable from `/plan` and the booking links on the dashboard
carry the trip's dates, guests and places over to the search pages.

## The Search Pages

The three search pages (flights, buses and trains, hotels) share the same
shape, so they behave the same way.

### Place suggestions

The From, To and Destination boxes are comboboxes
([`src/components/PlaceInput.jsx`](src/components/PlaceInput.jsx)). They
suggest places from two sources:

- a bundled list of Indian cities and airports
  ([`src/utils/places.js`](src/utils/places.js)), so the box is useful
  straight away and works offline;
- the backend's `GET /api/maps/geocode`, so a place that is not in the list
  can still be found.

Use the arrow keys to move through the suggestions, Enter to pick one, and
Escape to close the list. Whatever you type is still sent with the search, so
an unusual place name is never blocked.

### Concessions

A single-select group: None, Senior citizen, Army, Student, Doctor, Nurse
([`src/components/ConcessionSelect.jsx`](src/components/ConcessionSelect.jsx)).
It applies to flights, buses, trains and hotels. A traveller picks one
category, because a ticket is booked for one concession.

### Filters

[`src/components/FilterPanel.jsx`](src/components/FilterPanel.jsx) holds the
filters, and the sort dropdown sits above the results
([`src/components/SortSelect.jsx`](src/components/SortSelect.jsx)).

| Filter | Buses and trains | Flights | Hotels |
| --- | --- | --- | --- |
| AC / Non-AC | ✓ | | |
| Seater / Sleeper | ✓ | | |
| Live tracking only | ✓ | | |
| New vehicles only | ✓ | | |
| Price range | ✓ | ✓ | ✓ (per night) |
| Departure time | ✓ | ✓ | check-in time |
| Sort | ✓ | ✓ | ✓ |

The departure time filter is split into night (12am–6am), morning
(6am–12pm), afternoon (12pm–6pm) and evening (6pm–12am).

The panel is always open on a wide screen. On a narrow one it folds away
behind a button, so the form does not push the results off the screen.

### How filtering works

The filters are applied in two places on purpose:

- the **backend** filters the results it sends
  (`backend/app/services/filters.py`);
- the **page** filters them again
  ([`src/utils/resultFilters.js`](src/utils/resultFilters.js)).

So a filter takes effect straight away, without a round trip, and the sample
data behaves the same way the real backend does. The rules are written twice
because the backend has no JavaScript and the frontend has no Python — the two
must agree, and `backend/tests/test_filters.py` pins the backend side down.

Because the server also narrows the results, a filter that *widens* the
search (for example turning "AC" into "Non-AC") needs fresh results, so
changing a filter runs the search again
([`src/hooks/useFilterRefresh.js`](src/hooks/useFilterRefresh.js)). The run is
delayed by 400ms, so typing in the price boxes does not send a request for
every keystroke.

### Sorting

`Recommended` keeps the order the provider sent. The other options are price
low to high, price high to low, departure earliest first, departure latest
first, and shortest trip first. Hotels sort by name instead, since they have
no departure time.

## Project Structure

```
src/
├── components/
│   ├── PlaceInput.jsx       Combobox with place suggestions
│   ├── ConcessionSelect.jsx The concession radio group
│   ├── FilterPanel.jsx      The filter panel
│   ├── SortSelect.jsx       The sort dropdown above the results
│   ├── ResultsPanel.jsx     Loading, error, empty and results states
│   ├── TripForm.jsx         The trip creation form
│   ├── ItineraryCard.jsx    One day of the plan
│   ├── BudgetCard.jsx       The estimated costs
│   ├── ChatAssistant.jsx    The AI chat panel
│   ├── MapView.jsx          The map of the trip
│   └── BookingOptions.jsx   Links to the search pages
├── pages/
│   ├── Home.jsx  Plan.jsx  Dashboard.jsx
│   └── Flights.jsx  Transport.jsx  Hotels.jsx
├── hooks/
│   ├── useSearch.js         Runs a search and tracks its status
│   └── useFilterRefresh.js  Re-runs the search when the filters change
├── services/
│   ├── api.js               All the calls to the backend
│   ├── mockActions.js       The sample data
│   └── mockTrip.js          The sample trip
├── utils/
│   ├── filters.js           The filter options and the API shape
│   ├── resultFilters.js     Filtering and sorting on the page
│   ├── places.js            The bundled place list
│   ├── dates.js  format.js  queryPrefill.js  url.js
└── index.css                The design system
```

## Calling the Backend

All the calls live in [`src/services/api.js`](src/services/api.js). The pages
never call `fetch` directly.

Every call has the same behaviour: a 60 second timeout, and an error the page
can show. The error is either the message the server sent, or a plain sentence
saying the server could not be reached.

`searchFlights`, `searchHotels` and `searchTransport` take a `concession` and
a `filters` object, and send them with the search. The shape of `filters` is
in [`src/utils/filters.js`](src/utils/filters.js) (`toApiFilters`), and it
matches the contract in [`../docs/api-contract.md`](../docs/api-contract.md).

## Notes

- The app never takes payment. Every "Book" button opens the provider's own
  website, and only `https` URLs are allowed to become a link
  ([`src/utils/url.js`](src/utils/url.js)).
- Sample data is labelled as such on the page, so it is never mistaken for a
  real price.
- The map uses Leaflet with dark CARTO tiles, so it matches the rest of the
  interface without needing an image file.
