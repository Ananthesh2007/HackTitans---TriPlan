"""Tests for trip creation, retrieval, modification and budget.

Run with:
    cd backend
    .venv\\Scripts\\python.exe -m pytest tests/ -v
"""

import pytest


# --------------------------------------------------------------------------
# POST /api/trips
# --------------------------------------------------------------------------
class TestTripCreation:
    def test_returns_200(self, client, trip_payload):
        assert client.post("/api/trips", json=trip_payload).status_code == 200

    def test_trip_id_is_a_uuid(self, client, trip_payload):
        trip_id = client.post("/api/trips", json=trip_payload).json()["trip_id"]
        assert len(trip_id) == 36
        assert trip_id.count("-") == 4

    def test_echoes_the_request(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        for field in ("origin", "destination", "days", "people", "budget", "currency", "interests", "diet"):
            assert trip[field] == trip_payload.get(field, trip.get(field))
        assert trip["travel_date"] == trip_payload["travel_date"]

    def test_null_fields_are_excluded_from_the_response(self, client, trip_payload):
        # The routes use response_model_exclude_none=True.
        payload = {k: v for k, v in trip_payload.items() if k != "origin"}
        trip = client.post("/api/trips", json=payload).json()
        assert "origin" not in trip

    def test_currency_is_inr(self, client, trip_payload):
        assert client.post("/api/trips", json=trip_payload).json()["currency"] == "INR"

    def test_is_mock_true_without_an_ai_key(self, client, trip_payload):
        # No LLM_API_KEY is configured in the test environment.
        trip = client.post("/api/trips", json=trip_payload).json()
        assert trip["is_mock"] is True
        assert trip["warning"]

    def test_is_estimate_is_always_true(self, client, trip_payload):
        assert client.post("/api/trips", json=trip_payload).json()["is_estimate"] is True

    def test_origin_is_optional(self, client, trip_payload):
        payload = {k: v for k, v in trip_payload.items() if k != "origin"}
        response = client.post("/api/trips", json=payload)
        assert response.status_code == 200
        # Null fields are excluded from the response, so the key is absent.
        assert response.json().get("origin") is None

    @pytest.mark.parametrize("days", [1, 3, 7, 30])
    def test_itinerary_length_matches_days(self, client, trip_payload, days):
        trip = client.post("/api/trips", json={**trip_payload, "days": days}).json()
        assert len(trip["itinerary"]) == days

    def test_days_are_numbered_from_one(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        assert [d["day"] for d in trip["itinerary"]] == [1, 2, 3]

    def test_every_day_has_three_activities(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        assert all(len(d["activities"]) == 3 for d in trip["itinerary"])

    def test_activities_are_complete(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        for day in trip["itinerary"]:
            for activity in day["activities"]:
                assert activity["name"]
                assert activity["location"]
                assert activity["estimated_cost"] >= 0
                hours, minutes = activity["time"].split(":")
                assert 0 <= int(hours) <= 23
                assert 0 <= int(minutes) <= 59

    def test_activity_locations_carry_the_destination(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        for day in trip["itinerary"]:
            for activity in day["activities"]:
                assert activity["location"].endswith("Paris")

    def test_interests_may_be_empty(self, client, trip_payload):
        trip = client.post("/api/trips", json={**trip_payload, "interests": []}).json()
        assert trip["interests"] == []

    def test_diet_is_echoed(self, client, trip_payload):
        trip = client.post("/api/trips", json={**trip_payload, "diet": "vegan"}).json()
        assert trip["diet"] == "vegan"


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
class TestTripValidation:
    @pytest.mark.parametrize(
        "override",
        [
            {"days": 0},
            {"days": 31},
            {"budget": 0},
            {"budget": -100},
            {"people": 0},
            {"people": 21},
            {"destination": "P"},
            {"destination": "x" * 81},
            {"travel_date": "2020-01-01"},
            {"travel_date": "not-a-date"},
            {"travel_date": "2026-12-01T10:00:00"},
            {"interests": ["swimming"]},
            {"interests": ["nature"] * 9},
            {"diet": "keto"},
        ],
    )
    def test_rejects_bad_values(self, client, trip_payload, override):
        response = client.post("/api/trips", json={**trip_payload, **override})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"

    @pytest.mark.parametrize("missing", ["destination", "days", "budget", "people", "travel_date"])
    def test_rejects_missing_fields(self, client, trip_payload, missing):
        payload = {k: v for k, v in trip_payload.items() if k != missing}
        response = client.post("/api/trips", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"

    def test_rejects_malformed_json(self, client):
        response = client.post(
            "/api/trips", content=b"{not json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"

    def test_rejects_an_empty_body(self, client):
        assert client.post("/api/trips", content=b"").status_code == 422

    def test_rejects_a_json_array(self, client):
        assert client.post("/api/trips", json=[1, 2, 3]).status_code == 422

    def test_error_body_has_the_standard_shape(self, client, trip_payload):
        body = client.post("/api/trips", json={**trip_payload, "days": 0}).json()
        assert set(body) == {"error"}
        assert set(body["error"]) >= {"code", "message"}
        assert body["error"]["code"] == body["error"]["code"].lower()


# --------------------------------------------------------------------------
# GET /api/trips/{trip_id}
# --------------------------------------------------------------------------
class TestTripRetrieval:
    def test_returns_the_created_trip(self, client, created_trip):
        response = client.get(f"/api/trips/{created_trip['trip_id']}")
        assert response.status_code == 200
        assert response.json()["itinerary"] == created_trip["itinerary"]

    def test_missing_trip_returns_404(self, client):
        response = client.get("/api/trips/does-not-exist")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "trip_not_found"

    def test_a_very_long_id_is_handled(self, client):
        assert client.get("/api/trips/" + "a" * 500).status_code == 404

    @pytest.mark.parametrize(
        "trip_id", ["' OR '1'='1", "x'; DROP TABLE trips;--", "%20", "%E2%9C%93"]
    )
    def test_hostile_ids_are_handled_safely(self, client, trip_id):
        response = client.get(f"/api/trips/{trip_id}")
        assert response.status_code == 404
        assert "error" in response.json()


# --------------------------------------------------------------------------
# POST /api/trips/{trip_id}/modify
# --------------------------------------------------------------------------
class TestTripModification:
    def test_modify_with_conversation_history(self, client, created_trip):
        response = client.post(
            f"/api/trips/{created_trip['trip_id']}/modify",
            json={
                "message": "make that cheaper",
                "history": [
                    {"role": "user", "content": "Can we visit national parks?"},
                    {"role": "assistant", "content": "Yes, we have added a nature walk on day 1."},
                ],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["reply"], str) and body["reply"]
        assert body["trip"]["itinerary"]

    def test_the_proposed_trip_keeps_the_same_id(self, client, created_trip):
        response = client.post(
            f"/api/trips/{created_trip['trip_id']}/modify", json={"message": "add a museum"}
        )
        assert response.json()["trip"]["trip_id"] == created_trip["trip_id"]

    def test_missing_trip_returns_404(self, client):
        response = client.post("/api/trips/does-not-exist/modify", json={"message": "hi"})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "trip_not_found"

    @pytest.mark.parametrize("message", ["", "   ", "x" * 501])
    def test_rejects_a_bad_message(self, client, created_trip, message):
        response = client.post(
            f"/api/trips/{created_trip['trip_id']}/modify", json={"message": message}
        )
        assert response.status_code == 422


# --------------------------------------------------------------------------
# POST /api/trips/{trip_id}/budget
# --------------------------------------------------------------------------
class TestBudget:
    def test_returns_the_breakdown_and_status(self, client, created_trip):
        response = client.post(f"/api/trips/{created_trip['trip_id']}/budget")
        assert response.status_code == 200
        body = response.json()
        assert body["trip_id"] == created_trip["trip_id"]
        assert body["budget_status"]["budget"] == created_trip["budget"]
        assert body["budget_status"]["estimate"] == body["estimated_costs"]["total"]

    def test_total_equals_the_sum_of_the_lines(self, client, created_trip):
        costs = client.post(f"/api/trips/{created_trip['trip_id']}/budget").json()["estimated_costs"]
        lines = {k: v for k, v in costs.items() if k != "total"}
        assert costs["total"] == sum(lines.values())

    def test_activities_line_matches_the_plan(self, client, created_trip):
        # The activities line is the plan cost multiplied by the number of people.
        costs = created_trip["estimated_costs"]
        plan_sum = sum(
            a["estimated_cost"]
            for day in created_trip["itinerary"]
            for a in day["activities"]
        )
        assert costs["activities"] == plan_sum * created_trip["people"]

    def test_fixed_lines_scale_with_people_and_days(self, client, trip_payload):
        trip = client.post("/api/trips", json=trip_payload).json()
        costs = trip["estimated_costs"]
        assert costs["flights"] == 4800 * trip["people"]
        assert costs["accommodation"] == 2000 * trip["days"] * trip["people"]
        assert costs["food"] == 1000 * trip["days"] * trip["people"]
        assert costs["local_transport"] == 500 * trip["days"] * trip["people"]

    def test_over_budget_is_flagged(self, client, trip_payload):
        # A budget of 1 is below any realistic estimate.
        trip = client.post("/api/trips", json={**trip_payload, "budget": 1}).json()
        status = client.post(f"/api/trips/{trip['trip_id']}/budget").json()["budget_status"]
        assert status["is_below_estimate"] is True
        assert status["shortfall"] == status["estimate"] - 1
        assert "₹" in status["message"]

    def test_missing_trip_returns_404(self, client):
        response = client.post("/api/trips/does-not-exist/budget")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "trip_not_found"
