"""Tests for the flight, hotel and transport search endpoints."""

import pytest

FLIGHTS = {"origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2}
HOTELS = {"destination": "Paris", "check_in": "2026-12-01", "check_out": "2026-12-04", "guests": 2}
TRANSPORT = {"origin": "Mumbai", "destination": "Paris", "date": "2026-12-01", "passengers": 2, "mode": "train"}


class TestFlightSearch:
    def test_returns_200(self, client):
        assert client.post("/api/flights/search", json=FLIGHTS).status_code == 200

    def test_flags_mock_data(self, client):
        assert client.post("/api/flights/search", json=FLIGHTS).json()["is_mock"] is True

    def test_results_are_well_formed(self, client):
        results = client.post("/api/flights/search", json=FLIGHTS).json()["results"]
        assert results
        for result in results:
            assert result["id"]
            assert isinstance(result["price"], (int, float))
            assert result["price"] >= 0
            assert result["currency"] == "INR"

    def test_booking_urls_are_https_only(self, client):
        results = client.post("/api/flights/search", json=FLIGHTS).json()["results"]
        for result in results:
            if result.get("booking_url"):
                assert result["booking_url"].startswith("https://")

    def test_rejects_the_same_origin_and_destination(self, client):
        response = client.post("/api/flights/search", json={**FLIGHTS, "destination": "Mumbai"})
        assert response.status_code == 422

    @pytest.mark.parametrize("override", [{"date": "2020-01-01"}, {"passengers": 0}, {"passengers": 10}])
    def test_rejects_bad_values(self, client, override):
        response = client.post("/api/flights/search", json={**FLIGHTS, **override})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"

    def test_rejects_the_name_departure_date(self, client):
        # The contract uses "date", not "departure_date".
        response = client.post(
            "/api/flights/search",
            json={"origin": "Mumbai", "destination": "Paris", "departure_date": "2026-12-01", "passengers": 2},
        )
        assert response.status_code == 422


class TestHotelSearch:
    def test_returns_200(self, client):
        assert client.post("/api/hotels/search", json=HOTELS).status_code == 200

    def test_results_are_well_formed(self, client):
        results = client.post("/api/hotels/search", json=HOTELS).json()["results"]
        assert results
        for result in results:
            assert result["name"]
            assert isinstance(result["price_per_night"], (int, float))
            assert result["price_per_night"] >= 0

    def test_accepts_an_explicit_rooms_value(self, client):
        assert client.post("/api/hotels/search", json={**HOTELS, "rooms": 1}).status_code == 200

    @pytest.mark.parametrize(
        "override",
        [
            {"check_out": "2026-11-30"},   # check-out before check-in
            {"check_out": "2026-12-01"},   # check-out equal to check-in
            {"check_in": "2020-01-01"},    # check-in in the past
            {"guests": 0},
            {"guests": 21},
            {"rooms": 0},
            {"rooms": 11},
        ],
    )
    def test_rejects_bad_values(self, client, override):
        response = client.post("/api/hotels/search", json={**HOTELS, **override})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"


class TestTransportSearch:
    @pytest.mark.parametrize("mode", ["bus", "train"])
    def test_returns_results_for_each_mode(self, client, mode):
        response = client.post("/api/transport/search", json={**TRANSPORT, "mode": mode})
        assert response.status_code == 200
        body = response.json()
        assert body["is_mock"] is True
        assert body["results"]

    def test_bus_and_train_return_different_results(self, client):
        bus = client.post("/api/transport/search", json={**TRANSPORT, "mode": "bus"}).json()["results"]
        train = client.post("/api/transport/search", json={**TRANSPORT, "mode": "train"}).json()["results"]
        assert bus != train

    @pytest.mark.parametrize("override", [{"mode": "car"}, {"mode": "flight"}])
    def test_rejects_an_unknown_mode(self, client, override):
        response = client.post("/api/transport/search", json={**TRANSPORT, **override})
        assert response.status_code == 422

    def test_rejects_a_missing_mode(self, client):
        payload = {k: v for k, v in TRANSPORT.items() if k != "mode"}
        assert client.post("/api/transport/search", json=payload).status_code == 422


class TestBookingLinks:
    def test_flight_booking_link(self, client):
        body = client.post("/api/flights/booking-link", json={"flight_id": "flight-001"}).json()
        assert body["flight_id"] == "flight-001"
        assert body["booking_url"].startswith("https://")
        assert body["message"]

    def test_flight_booking_url_is_from_the_allowlist(self, client):
        from app.routes.flights import VERIFIED_AIRLINES

        body = client.post("/api/flights/booking-link", json={"flight_id": "flight-001"}).json()
        assert any(body["booking_url"].startswith(p) for p in VERIFIED_AIRLINES.values())

    def test_hotel_booking_link(self, client):
        body = client.post("/api/hotels/booking-link", json={"hotel_id": "hotel-001"}).json()
        assert body["hotel_id"] == "hotel-001"
        assert body["booking_url"].startswith("https://")

    def test_hotel_booking_url_is_from_the_allowlist(self, client):
        from app.routes.hotels import VERIFIED_HOTEL_PROVIDERS

        body = client.post("/api/hotels/booking-link", json={"hotel_id": "hotel-001"}).json()
        assert any(body["booking_url"].startswith(p) for p in VERIFIED_HOTEL_PROVIDERS.values())

    def test_a_caller_supplied_url_is_ignored(self, client):
        response = client.post(
            "/api/flights/booking-link",
            json={"flight_id": "f1", "booking_url": "http://evil.example.com"},
        )
        assert response.status_code == 200
        assert "evil.example.com" not in response.text

    @pytest.mark.parametrize("endpoint", ["/api/flights/booking-link", "/api/hotels/booking-link"])
    def test_requires_an_id(self, client, endpoint):
        response = client.post(endpoint, json={})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_input"

    @pytest.mark.parametrize("endpoint", ["/api/flights/booking-link", "/api/hotels/booking-link"])
    def test_rejects_an_empty_id(self, client, endpoint):
        response = client.post(endpoint, json={"flight_id": "", "hotel_id": ""})
        assert response.status_code == 400


class TestWeather:
    def test_returns_200(self, client):
        response = client.get("/api/weather", params={"place": "Coorg", "date": "2026-11-20"})
        assert response.status_code == 200

    def test_echoes_the_place_and_date(self, client):
        body = client.get("/api/weather", params={"place": "Coorg", "date": "2026-11-20"}).json()
        assert body["place"] == "Coorg"
        assert body["date"] == "2026-11-20"

    def test_says_the_service_is_not_configured(self, client):
        body = client.get("/api/weather", params={"place": "Coorg", "date": "2026-11-20"}).json()
        assert "error" in body
        # It must never invent weather data for a real place.
        assert "temperature" not in body

    def test_both_url_forms_work(self, client):
        for path in ("/api/weather", "/api/weather/"):
            response = client.get(path, params={"place": "Coorg", "date": "2026-11-20"})
            assert response.status_code == 200, path

    @pytest.mark.parametrize(
        "params",
        [
            {"date": "2026-11-20"},       # no place
            {"place": "Coorg"},           # no date
            {"place": "Coorg", "date": "2020-01-01"},   # past date
            {"place": "C", "date": "2026-11-20"},        # place too short
        ],
    )
    def test_rejects_bad_parameters(self, client, params):
        response = client.get("/api/weather", params=params)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"
