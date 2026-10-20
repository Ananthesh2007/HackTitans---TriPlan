"""Tests for error handling, HTTP behaviour, CORS and concurrency."""

import concurrent.futures

import pytest


class TestErrorFormat:
    """Every error must come back in the same JSON shape."""

    @pytest.mark.parametrize(
        "method,path,expected",
        [
            ("GET", "/api/trips", 405),
            ("PUT", "/health", 405),
            ("DELETE", "/health", 405),
            ("GET", "/api/trips/a/b/c", 404),
            ("GET", "/api/trips/does-not-exist", 404),
        ],
    )
    def test_standard_error_shape(self, client, method, path, expected):
        response = client.request(method, path)
        assert response.status_code == expected
        body = response.json()
        assert set(body) == {"error"}
        assert set(body["error"]) >= {"code", "message"}
        assert body["error"]["code"].islower()
        assert body["error"]["message"]

    def test_validation_errors_include_field_details(self, client, trip_payload):
        body = client.post("/api/trips", json={**trip_payload, "days": 0}).json()
        assert body["error"]["code"] == "invalid_input"
        assert body["error"]["details"]
        assert body["error"]["details"][0]["field"] == "days"

    def test_errors_never_leak_internals(self, client):
        body = client.get("/api/trips/does-not-exist").json()
        text = str(body).lower()
        for leak in ("traceback", "exception", "sqlite", "select ", "file \""):
            assert leak not in text


class TestCors:
    def test_allows_the_configured_origin(self, client):
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_does_not_echo_a_foreign_origin(self, client):
        response = client.get("/health", headers={"Origin": "http://evil.example.com"})
        assert response.headers.get("access-control-allow-origin") is None

    def test_preflight_is_allowed(self, client):
        response = client.options(
            "/api/trips",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert "POST" in response.headers.get("access-control-allow-methods", "")


class TestConcurrency:
    def test_parallel_trip_creations_all_succeed(self, client, trip_payload):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            futures = [
                pool.submit(
                    client.post, "/api/trips", json={**trip_payload, "budget": 15000 + i}
                )
                for i in range(20)
            ]
            codes = [f.result().status_code for f in futures]
        assert set(codes) == {200}

    def test_parallel_creations_get_unique_ids(self, client, trip_payload):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(client.post, "/api/trips", json=trip_payload) for _ in range(10)]
            ids = {f.result().json()["trip_id"] for f in futures}
        assert len(ids) == 10

    def test_a_trip_stays_readable_after_parallel_writes(self, client, created_trip):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(lambda _: client.post("/api/trips", json={
                "origin": "Mumbai", "destination": "Paris", "days": 2,
                "budget": 10000, "people": 1, "travel_date": "2026-12-01"}), range(10)))
        assert client.get(f"/api/trips/{created_trip['trip_id']}").status_code == 200


class TestContract:
    """Guards against the server running stale code."""

    def test_the_trip_route_is_not_named_get_trip(self, client):
        # An old version named the route handler "get_trip", which shadowed the
        # imported store function and caused infinite recursion (HTTP 500).
        schema = client.get("/openapi.json").json()
        assert "retrieve_trip_api_trips__trip_id__get" in str(schema)

    def test_all_endpoints_are_registered(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        for path in (
            "/health",
            "/api/trips",
            "/api/trips/{trip_id}",
            "/api/trips/{trip_id}/modify",
            "/api/trips/{trip_id}/budget",
            "/api/flights/search",
            "/api/flights/booking-link",
            "/api/hotels/search",
            "/api/hotels/booking-link",
            "/api/transport/search",
            "/api/weather",
        ):
            assert path in paths, path

    def test_health_reports_the_service_name(self, client):
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["service"] == "triplan-backend"
        assert "environment" in body
