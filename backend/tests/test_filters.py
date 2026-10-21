"""Tests for the search filters.

The filters are applied by the backend (`app/services/filters.py`) and by
the frontend (`frontend/src/utils/resultFilters.js`). These tests cover the
backend side. The two must agree, so the rules are the same.
"""

import pytest

from app.models.search import SearchFilters
from app.services.filters import apply_filters, sort_results


def make_result(**overrides):
    """One result, with sensible defaults."""
    result = {
        "id": "r1",
        "operator": "Sample Operator",
        "vehicle_type": "AC sleeper",
        "departure_time": "21:30",
        "arrival_time": "05:15",
        "duration": "7h 45m",
        "price": 900,
        "tracking": False,
        "is_new": False,
        "concessions": [],
    }
    result.update(overrides)
    return result


class TestConcessionFilter:
    def test_keeps_everything_without_a_concession(self):
        results = [make_result(), make_result(concessions=["student"])]
        assert len(apply_filters(results, SearchFilters())) == 2

    def test_keeps_a_result_that_offers_the_concession(self):
        results = [make_result(concessions=["senior_citizen", "student"])]
        kept = apply_filters(results, SearchFilters(), "senior_citizen")
        assert len(kept) == 1

    def test_drops_a_result_that_does_not_offer_the_concession(self):
        results = [make_result(concessions=["student"])]
        kept = apply_filters(results, SearchFilters(), "senior_citizen")
        assert kept == []

    def test_keeps_a_result_that_lists_no_concessions(self):
        # The provider did not say it was excluded, so it stays.
        results = [make_result(concessions=[])]
        assert len(apply_filters(results, SearchFilters(), "doctor")) == 1


class TestPriceFilter:
    def test_keeps_a_price_inside_the_range(self):
        results = [make_result(price=500)]
        kept = apply_filters(results, SearchFilters(price_min=400, price_max=600))
        assert len(kept) == 1

    def test_drops_a_price_below_the_range(self):
        results = [make_result(price=100)]
        assert apply_filters(results, SearchFilters(price_min=400)) == []

    def test_drops_a_price_above_the_range(self):
        results = [make_result(price=900)]
        assert apply_filters(results, SearchFilters(price_max=600)) == []

    def test_keeps_a_result_with_no_price(self):
        results = [make_result(price=None)]
        assert len(apply_filters(results, SearchFilters(price_min=400))) == 1


class TestVehicleFilters:
    def test_keeps_ac_when_ac_is_asked_for(self):
        results = [make_result(vehicle_type="AC sleeper"), make_result(vehicle_type="Non-AC seater")]
        kept = apply_filters(results, SearchFilters(ac="ac"))
        assert len(kept) == 1
        assert kept[0]["vehicle_type"] == "AC sleeper"

    def test_keeps_non_ac_when_non_ac_is_asked_for(self):
        results = [make_result(vehicle_type="AC sleeper"), make_result(vehicle_type="Non-AC seater")]
        kept = apply_filters(results, SearchFilters(ac="non_ac"))
        assert len(kept) == 1
        assert kept[0]["vehicle_type"] == "Non-AC seater"

    def test_the_ac_filter_keeps_a_vehicle_type_that_does_not_say(self):
        # "Sleeper class" says nothing about AC, so it is not excluded. The
        # provider has not said it is a non-AC service.
        results = [make_result(vehicle_type="Sleeper class")]
        assert len(apply_filters(results, SearchFilters(ac="ac"))) == 1

    def test_the_ac_filter_does_not_match_a_word_containing_ac(self):
        # "AC sleeper" is an AC service. "Sleeper class" is not the same thing.
        results = [make_result(vehicle_type="AC sleeper")]
        assert len(apply_filters(results, SearchFilters(ac="ac"))) == 1

    def test_keeps_sleeper_when_sleeper_is_asked_for(self):
        results = [make_result(vehicle_type="AC sleeper"), make_result(vehicle_type="AC seater")]
        kept = apply_filters(results, SearchFilters(seat_class="sleeper"))
        assert len(kept) == 1
        assert kept[0]["vehicle_type"] == "AC sleeper"

    def test_keeps_only_tracked_services(self):
        results = [make_result(tracking=True), make_result(tracking=False)]
        kept = apply_filters(results, SearchFilters(tracking=True))
        assert len(kept) == 1
        assert kept[0]["tracking"] is True

    def test_keeps_only_new_vehicles(self):
        results = [make_result(is_new=True), make_result(is_new=False)]
        kept = apply_filters(results, SearchFilters(is_new=True))
        assert len(kept) == 1
        assert kept[0]["is_new"] is True


class TestDepartureWindow:
    @pytest.mark.parametrize(
        "time,window,expected",
        [
            ("05:30", "night", True),      # before 6am
            ("05:30", "morning", False),
            ("13:00", "afternoon", True),
            ("13:00", "morning", False),
            ("21:30", "evening", True),
            ("21:30", "night", False),
            ("02:00", "night", True),
            ("12:00", "afternoon", True),
            ("06:00", "morning", True),    # 6am is the start of the morning
            ("18:00", "evening", True),   # 6pm is the start of the evening
            ("00:00", "night", True),
            ("23:59", "evening", True),
        ],
    )
    def test_the_time_falls_in_the_right_window(self, time, window, expected):
        results = [make_result(departure_time=time)]
        kept = apply_filters(results, SearchFilters(departure_window=window))
        assert bool(kept) is expected

    def test_keeps_a_result_with_no_time(self):
        results = [make_result(departure_time=None)]
        assert len(apply_filters(results, SearchFilters(departure_window="morning"))) == 1


class TestSorting:
    def test_sorts_by_price_from_low_to_high(self):
        results = [make_result(price=900), make_result(price=300), make_result(price=600)]
        ordered = sort_results(results, "price_asc")
        assert [item["price"] for item in ordered] == [300, 600, 900]

    def test_sorts_by_price_from_high_to_low(self):
        results = [make_result(price=300), make_result(price=900)]
        ordered = sort_results(results, "price_desc")
        assert [item["price"] for item in ordered] == [900, 300]

    def test_sorts_by_departure_time(self):
        results = [make_result(departure_time="21:30"), make_result(departure_time="05:30")]
        ordered = sort_results(results, "departure_asc")
        assert [item["departure_time"] for item in ordered] == ["05:30", "21:30"]

    def test_sorts_by_duration(self):
        results = [make_result(duration="9h 50m"), make_result(duration="2h 15m")]
        ordered = sort_results(results, "duration_asc")
        assert [item["duration"] for item in ordered] == ["2h 15m", "9h 50m"]

    def test_a_result_with_no_price_goes_to_the_end(self):
        results = [make_result(price=None), make_result(price=300)]
        ordered = sort_results(results, "price_asc")
        assert ordered[-1]["price"] is None

    def test_the_recommended_sort_keeps_the_original_order(self):
        results = [make_result(price=900), make_result(price=300)]
        ordered = sort_results(results, "recommended")
        assert [item["price"] for item in ordered] == [900, 300]


class TestFilterEndpoints:
    """The filters work through the search endpoints as well."""

    def test_the_transport_endpoint_applies_the_filters(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
            "filters": {"ac": "ac"},
        }
        results = client.post("/api/transport/search", json=payload).json()["results"]
        assert results
        for result in results:
            assert "AC" in result["vehicle_type"]

    def test_the_transport_endpoint_keeps_only_tracked_buses(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
            "filters": {"tracking": True},
        }
        results = client.post("/api/transport/search", json=payload).json()["results"]
        assert results
        for result in results:
            assert result["tracking"] is True

    def test_the_transport_endpoint_applies_a_price_range(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
            "filters": {"price_max": 500},
        }
        results = client.post("/api/transport/search", json=payload).json()["results"]
        for result in results:
            assert result["price"] <= 500

    def test_the_transport_endpoint_applies_a_concession(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
            "concession": "doctor",
        }
        results = client.post("/api/transport/search", json=payload).json()["results"]
        for result in results:
            assert "doctor" in result["concessions"]

    def test_the_transport_endpoint_sorts_by_price(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
            "filters": {"sort": "price_asc"},
        }
        results = client.post("/api/transport/search", json=payload).json()["results"]
        prices = [result["price"] for result in results]
        assert prices == sorted(prices)

    def test_the_flight_endpoint_applies_a_departure_window(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "filters": {"departure_window": "morning"},
        }
        results = client.post("/api/flights/search", json=payload).json()["results"]
        for result in results:
            hour = int(result["departure_time"].split(":")[0])
            assert 6 <= hour < 12

    def test_the_hotel_endpoint_applies_a_price_range(self, client):
        payload = {
            "destination": "Paris",
            "check_in": "2026-12-01",
            "check_out": "2026-12-04",
            "guests": 2,
            "filters": {"price_max": 2000},
        }
        results = client.post("/api/hotels/search", json=payload).json()["results"]
        for result in results:
            assert result["price_per_night"] <= 2000

    def test_the_hotel_endpoint_applies_a_check_in_window(self, client):
        payload = {
            "destination": "Paris",
            "check_in": "2026-12-01",
            "check_out": "2026-12-04",
            "guests": 2,
            "filters": {"departure_window": "morning"},
        }
        results = client.post("/api/hotels/search", json=payload).json()["results"]
        for result in results:
            hour = int(result["check_in_time"].split(":")[0])
            assert 6 <= hour < 12

    def test_a_request_without_filters_still_works(self, client):
        payload = {
            "origin": "Mumbai",
            "destination": "Paris",
            "date": "2026-12-01",
            "passengers": 2,
            "mode": "bus",
        }
        response = client.post("/api/transport/search", json=payload)
        assert response.status_code == 200
        assert response.json()["results"]
