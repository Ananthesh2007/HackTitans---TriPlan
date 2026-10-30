# TriPlan — AI-Powered Travel Planner

**Project type:** Agentic AI Travel Planner  
**Team size:** 3 members  
**Primary goal:** Build a website that generates and modifies personalised travel itineraries, estimates trip expenses, and helps users search flights and hotels with external booking redirection.

## Quick Start

```bash
# Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

#or
python -m venv .venv #download .venv if not installed or else backend will not run (Using python 3.13.16)
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload # after doing all the above steps run this

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Access:** Frontend at `http://localhost:5173`, Backend at `http://localhost:8000`

**Documentation:** 
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Refactor Summary](REFACTOR_SUMMARY.md)
- [Frontend Refactor Details](FRONTEND_REFACTOR.md)

## 1. Project Overview

TriPlan is an AI-powered travel-planning website that helps users plan a trip in one place. It generates personalised day-wise itineraries, estimates expenses, suggests routes and activities, supports weather-aware recommendations, and provides flight and hotel search workflows. Users can modify the itinerary through natural-language chat.

For flight and hotel bookings, the prototype can redirect users to verified airline, hotel, or authorised booking-provider websites. The external provider handles the actual reservation, payment, and confirmation.

### Current Status 

✅ **Fully Functional MVP** - Core trip planning, AI chat, and booking workflows complete  
✅ **Ocean Wanderlust UI** - Modern glassmorphic design with Framer Motion animations  
✅ **Real Travel Data** - Integration-ready for Amadeus (flights) and Tavily (hotels)  
✅ **Optimized Performance** - 15s LLM timeout, 330ms frontend build, 191kB gzipped bundle  
✅ **Comprehensive Testing** - 28 backend tests passing, full integration verified  

See [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) and [FRONTEND_REFACTOR.md](FRONTEND_REFACTOR.md) for detailed documentation.

## 2. Main Features

### 2.1 AI Trip Planner

- Accept destination, travel dates, duration, number of travellers, budget, interests, and food preferences.
- Generate a personalised day-wise itinerary.
- Suggest activities, places, and approximate timings.
- Return structured itinerary data that the website can display.

### 2.2 Smart Budget Planner

- Estimate flights, accommodation, food, activities, and local transport.
- Calculate total estimated trip expenses.
- Compare estimated expenses against the user’s budget.
- Recalculate costs when the itinerary changes.
- Clearly label estimates and avoid presenting AI guesses as confirmed prices.

### 2.3 Flight Search and Booking Redirection

- Accept departure city, destination, date, and passenger count.
- Display flight information from a supported provider when integrated.
- Show airline, timings, stops, fares, and booking links when the provider supplies those fields.
- Provide a **Book Now** button that opens a verified airline or authorised booking-provider URL.
- Let the external provider handle booking, payment, and ticket confirmation.

### 2.4 Hotel Search and Booking Redirection

- Accept destination, check-in date, check-out date, guests, and room count.
- Display hotel information from a supported provider when integrated.
- Show location, amenities, ratings, room details, rates, and booking links when available.
- Provide a **Book Now** button that opens a verified hotel or authorised booking-platform URL.
- Let the external provider handle reservations and payment.

### 2.5 Smart Route Planning

- Group nearby attractions.
- Suggest a practical visiting order.
- Display places and routes on a map.
- Reduce unnecessary travel between activities using real route data where available.

### 2.6 Weather-Aware Itinerary

- Retrieve weather information from a weather API.
- Suggest indoor alternatives when conditions are unsuitable for outdoor activities.
- Use forecast information only when available; do not fabricate live weather.

### 2.7 AI Travel Assistant

- Modify an itinerary through natural-language instructions.
- Example: “Remove museums and add more adventure activities.”
- Update activities, timings, routes, and estimated costs.
- Answer questions using the current trip context.

### 2.8 Group Travel Planner

- Collect preferences from multiple travellers.
- Consider different interests, budgets, and food preferences.
- Generate a shared plan from the submitted preferences.

### 2.9 Food Recommendations

- Suggest food and restaurants according to budget and preferences.
- Support vegetarian, local-food, and affordable-food preferences.
- Include location and other details when reliable data is available.

### 2.10 Alternative Activities / Nearby Assistant

- Suggest alternative activities when a planned place is unavailable, if reliable data is available.
- With permission-based location access, suggest nearby activities.
- Answer requests such as “What can I do near me for the next three hours?”
- Consider available time and budget.

## 3. Technology Stack (Implemented)

| Component       | Technology Used                                      | Status                        |
|-----------------|------------------------------------------------------|-------------------------------|
| Frontend        | React 19 + Vite                                      | ✅ Complete                   |
| Styling         | Tailwind CSS v4 + Ocean Wanderlust theme            | ✅ Complete                   |
| Animations      | Framer Motion                                        | ✅ Complete                   |
| Backend         | Python + FastAPI                                     | ✅ Complete                   |
| AI              | OpenAI API or Gemini API                             | ✅ Complete                   |
| Agent workflow  | LLM tool/function calling                            | ✅ Complete                   |
| Database        | In-memory store (persistent DB optional)             | ✅ MVP Complete               |
| Maps            | OpenStreetMap + Leaflet                              | ✅ Complete (no key needed)   |
| Weather         | Weather API integration ready                        | ⚙️ Integration-ready          |
| Flight data     | Amadeus GDS (ready) + realistic fallback             | ⚙️ Integration-ready          |
| Hotel data      | Tavily Partner (ready) + realistic fallback          | ⚙️ Integration-ready          |
| Authentication  | Optional (not implemented)                           | ⬜ Future enhancement         |
| Version control | Git + GitHub                                         | ✅ Complete                   |
| Deployment      | Vercel/Render ready                                  | ✅ Ready to deploy            |

The backend uses realistic mock data (real carrier names, hotels, routes) until live API keys are configured. This allows full-stack development without provider dependencies.

## 4. System Architecture

1.  **User:** Enters trip details, searches flights/hotels, or chats with the assistant.
2.  **React frontend:** Provides the trip form, dashboard, AI chat, budget, map, flight search, and hotel search.
3.  **FastAPI backend:** Validates requests, manages trip data, and connects AI and external services.
4.  **AI coordinator:** Generates or modifies itineraries and decides which available tools to call.
5.  **Tools and services:** Budget calculator, maps, weather, flight search, and hotel search.
6.  **Database:** Stores users, trips, and saved plans if persistence is implemented.
7.  **Dashboard:** Displays itinerary, estimated costs, routes, and available search results.

**Important:** Live fares, hotel rates, availability, weather, opening hours, and route data must come from suitable data providers. AI-generated information must be labelled as a suggestion or estimate. Do not fabricate live results. External providers handle booking, payment, and confirmation.

## 5. Divide the Work Among Three Members

### Member 1 — Frontend Developer

**Main technologies:** HTML, CSS, JavaScript, React, Tailwind CSS.

Responsibilities:

- Build homepage and navigation.
- Build trip creation form.
- Develop itinerary dashboard and activity cards.
- Create AI chat interface.
- Build budget summary and map display.
- Create flight and hotel search forms and result cards.
- Implement external booking redirection.
- Connect the frontend to backend APIs.
- Improve responsive design and user experience.


### Member 2 — Backend Developer

**Main technologies:** Python, FastAPI, REST APIs, SQL/Firebase.

Responsibilities:

- Create FastAPI backend and REST endpoints.
- Connect frontend requests to backend services.
- Integrate AI, maps, weather, flight, and hotel providers.
- Implement budget calculations and input validation.
- Handle verified booking links.
- Set up database and authentication if included.
- Handle errors, environment variables, security, and deployment.


### Member 3 — AI Developer

**Main technologies:** Python basics, LLM API, prompt engineering, JSON schemas, tool calling.

Responsibilities:

- Integrate the selected LLM API.
- Create prompts for personalised itinerary generation.
- Generate structured JSON responses.
- Implement natural-language itinerary modifications.
- Build tool-calling workflows for budget, route, and weather tasks.
- Work with the backend developer on itinerary validation and re-planning.
- Test AI output for unsupported claims and inconsistent plans.


All members should participate in GitHub collaboration, API design, integration, testing, deployment, and the final presentation.

## 6. Thirty-Day Development Schedule

### Week 1 — Learn and Set Up (Days 1–7)

**Goal:** Basic frontend, backend, and AI output.

**Day 1 — All members**

- Install VS Code, Python, Node.js, and Git.
- Create the GitHub repository.
- Agree on the MVP, draw the workflow, and assign responsibilities.
- **Deliverable:** Repository, task ownership, and initial project structure.


**Day 2**

- Member 1: Learn HTML/CSS and build a basic homepage and trip form.
- Member 2: Learn Python basics and set up a simple FastAPI server.
- Member 3: Test LLM prompts that generate a sample itinerary.
- **Deliverable:** Basic homepage, running backend, and sample AI output.


**Day 3**

- Member 1: Add JavaScript form handling and validation.
- Member 2: Create an endpoint that receives trip details as JSON.
- Member 3: Define the structured JSON format for itinerary output.
- **Deliverable:** Working form, endpoint, and agreed itinerary schema.


**Days 4–5 — All members**

- Learn React, API requests, and JSON handling.
- Create initial React components.
- Agree on request/response schemas.
- **Deliverable:** Frontend components and documented API contract.


**Days 6–7 — All members**

- Build the basic form and itinerary screen.
- Test the backend.
- Verify sample AI output.
- **Deliverable:** Initial end-to-end prototype.


### Week 2 — Build the Core AI Planner (Days 8–14)

**Goal:** Generate and display personalised itineraries.

**Days 8–9**

- Member 1: Build trip form, loading states, error messages, and itinerary cards.
- Member 2: Build FastAPI endpoints and connect frontend to backend.
- Member 3: Connect the LLM API and generate structured itinerary JSON.
- **Deliverable:** User can submit a trip and receive an itinerary.


**Days 10–11**

- Member 1: Display day-wise activities, timings, locations, and estimated costs.
- Member 2: Validate requests and responses; handle API failures and return consistent JSON.
- Member 3: Improve prompts and handle malformed AI responses.
- **Deliverable:** More reliable itinerary dashboard.


**Days 12–14 — All members**

- Integrate the trip creation flow.
- Test different destinations, budgets, durations, and interests.
- Fix major issues.
- **Deliverable:** Functional core AI planner.


### Week 3 — Budget, AI Chat, Flights, and Hotels (Days 15–21)

**Goal:** Modify trips and implement booking redirection.

**Days 15–16**

- Member 1: Create AI chat UI and show revised itineraries.
- Member 2: Create itinerary-modification endpoint and deterministic budget calculations.
- Member 3: Implement natural-language modification while retaining trip context.
- **Deliverable:** User can request and see itinerary changes.


**Days 17–18**

- Member 1: Build budget summary, flight form, hotel form, and result cards.
- Member 2: Implement external airline/hotel search redirects using verified URLs; investigate suitable live-data providers.
- Member 3: Implement tool calling for budget and route tasks; validate updated plans.
- **Deliverable:** Budget interface and working external search/booking redirects.


**Days 19–21 — All members**

- Integrate and test flight and hotel redirection.
- If provider access is available, integrate live search results and booking links.
- **Deliverable:** Flight/hotel workflow with accurate capability labels and external links.


### Week 4 — Advanced Features, Testing, and Deployment (Days 22–30)

**Goal:** Complete and demonstrate a working prototype.

**Days 22–23**

- Member 1: Polish responsive UI, booking buttons, search results, and dashboard.
- Member 2: Integrate weather and maps if accessible; add optional database persistence and secure API configuration.
- Member 3: Add weather-aware suggestions and alternative activities using available data.
- **Deliverable:** Polished core app with selected live integrations.


**Days 24–25 — All members**

- Add food recommendations and group preferences if the core system is stable.
- **Deliverable:** Selected enhanced features.


**Day 26**

- Members 1 and 2: Implement and test saved trips if database integration is in scope.
- **Deliverable:** Persistence feature or documented decision to defer it.


**Day 27 — All members**

- Test trip generation, modification, budget calculations, redirects, and API failures.
- **Deliverable:** Test results and a prioritised bug list.


**Day 28**

- Members 1 and 2: Deploy frontend and backend and test the live website.
- **Deliverable:** Deployed prototype.


**Day 29 — All members**

- Prepare presentation, architecture diagram, feature descriptions, and demo script.
- **Deliverable:** Presentation and demo-ready build.


**Day 30 — All members**

- Perform final testing, fix critical bugs, and rehearse the demonstration.
- **Deliverable:** Final prototype and presentation.


## 7. Flight and Hotel Booking Workflows

### Flight workflow

1.  User enters departure city, destination, date, and passenger count.
2.  Retrieve flight results from a supported provider, if integrated.
3.  Display flight details supplied by the provider.
4.  User selects a flight and clicks **Book Now**.
5.  Open a verified airline or authorised booking provider’s website.
6.  User completes booking and payment externally.

### Hotel workflow

1.  User enters destination, check-in/out dates, guests, and rooms.
2.  Retrieve hotel information from a supported provider, if integrated.
3.  Display hotel details supplied by the provider.
4.  User selects a hotel and clicks **Book Now**.
5.  Open a verified hotel or authorised booking platform.
6.  User confirms the room and completes payment externally.

**Prototype approach:** Start with verified external search/booking redirects. Live listings require suitable provider access, and some providers restrict use of booking links. Do not collect payment details or claim a reservation has been completed unless a supported integration actually confirms it.

## 8. Agentic AI Workflow

The AI should understand the request, choose supported tools, and update the trip plan rather than merely returning a fixed itinerary.

1.  User enters trip details.
2.  FastAPI validates the input.
3.  AI coordinator receives the validated trip context.
4.  AI generates an itinerary and requests supported tools as needed.
5.  Backend tools calculate the budget and retrieve route/weather data.
6.  Backend validates the plan against the trip constraints.
7.  If the plan fails validation, revise it or return a clear limitation.
8.  Display the plan on the dashboard.
9.  User requests a modification.
10. AI uses the current trip context and tools to propose an update.
11. User can review the revised itinerary.
12. Flight and hotel searches lead to external booking pages.

### Suggested backend functions

- `generate_itinerary()` — Generate a day-wise plan.
- `estimate_budget()` — Calculate estimated trip costs.
- `get_route()` — Retrieve route and distance information.
- `get_weather()` — Retrieve weather information.
- `modify_itinerary()` — Update the plan from a user request.
- `validate_plan()` — Validate structure and constraints.
- `search_flights()` — Retrieve results from a supported provider.
- `get_flight_booking_url()` — Return a verified flight booking URL.
- `search_hotels()` — Retrieve results from a supported provider.
- `get_hotel_booking_url()` — Return a verified hotel booking URL.

Use deterministic backend code for calculations and validation. The AI can decide which supported functions to call, but must not invent results from unavailable services.

## 9. Backend API Structure

| Method | Endpoint                      | Purpose                                               |
|--------|-------------------------------|-------------------------------------------------------|
| POST   | `/api/trips`                  | Create a trip and generate itinerary                  |
| GET    | `/api/trips/{trip_id}`        | Retrieve a saved trip                                 |
| POST   | `/api/trips/{trip_id}/modify` | Modify itinerary                                      |
| POST   | `/api/trips/{trip_id}/budget` | Calculate/recalculate budget                          |
| POST   | `/api/trips/{trip_id}/route`  | Retrieve route information                            |
| GET    | `/api/weather`                | Retrieve weather information                          |
| POST   | `/api/flights/search`         | Search available flights                              |
| POST   | `/api/flights/booking-link`   | Get a supported flight booking URL                    |
| POST   | `/api/hotels/search`          | Search hotels                                         |
| POST   | `/api/hotels/booking-link`    | Get a supported hotel booking URL                     |
| GET    | `/api/users/trips`            | Retrieve saved trips if authentication is implemented |

### Example trip request

    {
      "destination": "Coorg",
      "days": 3,
      "budget": 15000,
      "people": 2,
      "travel_date": "2026-11-20",
      "interests": ["nature", "food", "adventure"],
      "diet": "vegetarian"
    }

### Example flight search request

    {
      "origin": "Mangalore",
      "destination": "New York",
      "date": "2026-11-20",
      "passengers": 1
    }

### Example hotel search request

    {
      "destination": "New York",
      "check_in": "2026-11-20",
      "check_out": "2026-11-23",
      "guests": 2,
      "rooms": 1
    }

These are proposed API formats. The team must agree on exact schemas before integration.

## 10. Website Pages

1.  **Home page:** Branding, navigation, trip search, feature introduction, optional sign-in.
2.  **Trip creation page:** Destination, dates, duration, travellers, budget, interests, dietary preferences, generate button.
3.  **Trip dashboard:** Day-wise itinerary, activities, estimated expenses, routes/map, weather/food suggestions, edit and save options.
4.  **Flight search page:** Departure, destination, date, passengers, provider-backed results, external booking buttons.
5.  **Hotel search page:** Destination, check-in/out, guests, rooms, provider-backed results, external booking buttons.
6.  **AI assistant:** Natural-language chat, itinerary changes, questions about the current plan, review of suggested changes.
7.  **My trips page (optional):** Saved trips and previous itineraries.

## 11. Recommended Project Folder Structure

    TriPlan/
    ├── frontend/
    │   ├── public/
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── Navbar.jsx
    │   │   │   ├── TripForm.jsx
    │   │   │   ├── ItineraryCard.jsx
    │   │   │   ├── BudgetCard.jsx
    │   │   │   ├── FlightCard.jsx
    │   │   │   ├── HotelCard.jsx
    │   │   │   └── ChatAssistant.jsx
    │   │   ├── pages/
    │   │   │   ├── Home.jsx
    │   │   │   ├── Dashboard.jsx
    │   │   │   ├── Flights.jsx
    │   │   │   ├── Hotels.jsx
    │   │   │   └── MyTrips.jsx
    │   │   ├── services/
    │   │   │   └── api.js
    │   │   ├── App.jsx
    │   │   └── main.jsx
    │   └── package.json
    ├── backend/
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── routes/
    │   │   │   ├── trips.py
    │   │   │   ├── flights.py
    │   │   │   ├── hotels.py
    │   │   │   └── weather.py
    │   │   ├── ai/
    │   │   │   ├── coordinator.py
    │   │   │   ├── prompts.py
    │   │   │   └── tools.py
    │   │   ├── services/
    │   │   │   ├── budget.py
    │   │   │   ├── maps.py
    │   │   │   ├── flights.py
    │   │   │   └── hotels.py
    │   │   ├── models/
    │   │   └── validators/
    │   ├── requirements.txt
    │   └── .env.example
    ├── docs/
    │   ├── api-contract.md
    │   └── architecture.md
    └── README.md

## 12. Development Checklist

### Phase 1 — Essential MVP ✅ COMPLETE

- [x] Responsive home page and trip form
- [x] AI-generated day-wise itinerary
- [x] Trip dashboard with Ocean Wanderlust theme
- [x] Estimated budget calculation with itemized breakdown
- [x] Natural-language itinerary modification
- [x] Itinerary validation and error handling
- [x] Flight external search redirect with filters
- [x] Hotel external search redirect with filters
- [x] Bus/train search with comprehensive filters

### Phase 2 — Enhanced Planner ✅ MOSTLY COMPLETE

- [x] Map and route integration (OpenStreetMap + Leaflet)
- [x] Glassmorphic UI with Framer Motion animations
- [x] Real travel data (carrier names, hotels, booking links)
- [ ] Weather-aware suggestions (integration-ready)
- [x] Food recommendations (in itinerary generation)
- [ ] Live flight search integration (Amadeus-ready)
- [ ] Live hotel search integration (Tavily-ready)
- [x] In-memory trip storage (persistent DB optional)

### Phase 3 — Advanced Features ⬜ FUTURE

- [ ] Group preference collection
- [ ] Nearby live trip assistant
- [ ] Alternative plans for unavailable activities
- [ ] Advanced multi-tool agent workflow
- [ ] User authentication and accounts
- [ ] Persistent database with saved trips

## 13. Testing Plan

| Test case                       | Expected result                                  |
|---------------------------------|--------------------------------------------------|
| Valid trip details              | AI generates structured itinerary                |
| Missing destination             | Validation message appears                       |
| Budget below estimated expenses | System identifies the mismatch                   |
| User removes museums            | Itinerary is updated accordingly                 |
| User changes trip duration      | Itinerary is revised                             |
| AI returns invalid JSON         | Backend handles the error without crashing       |
| Weather service unavailable     | No fabricated weather forecast is shown          |
| Flight provider unavailable     | Show a clear message or external search option   |
| Hotel provider unavailable      | Show a clear message or external search option   |
| User clicks flight Book Now     | Verified external flight booking page opens      |
| User clicks hotel Book Now      | Verified external hotel booking page opens       |
| External booking fails          | Show an appropriate error/unavailability message |
| Database fails                  | Do not falsely tell the user the trip was saved  |

## 14. Final Project Demonstration

1.  Enter destination, travel dates, budget, number of people, interests, and food preferences.
2.  Generate a personalised itinerary using AI.
3.  View itinerary, routes, and estimated budget.
4.  Modify the itinerary through AI chat.
5.  Search flights and demonstrate external airline booking redirection.
6.  Search hotels and demonstrate external hotel booking redirection.
7.  Show weather, food, and group-planning features if integrated.

## 15. Final Scope and Priorities

### Core deliverable

An AI trip planner with flight and hotel booking redirection. Users can create a trip, generate and modify an itinerary, view estimated costs, and open external flight and hotel booking pages.

### Build first

- Trip creation and AI itinerary generation
- Itinerary dashboard
- Budget estimation
- AI itinerary modification
- Flight search redirection
- Hotel search redirection

### Add if time and provider access allow

- Live flight and hotel results
- Maps and route optimisation
- Weather and food recommendations
- Saved trips and group planning
- Nearby live trip assistant

The main development objective is to make the end-to-end trip-planning workflow functional, rather than attempting every advanced feature at once. Flight and hotel redirection lets TriPlan support reservations without building its own payment or ticketing system.


## Note

For now we are using only geniune hotels, flights, buses and trains and no local shops.
