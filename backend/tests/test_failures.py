"""Tests for failure scenarios: AI provider problems and database problems.

The AI tests run the app in a separate process with a stub provider, because
the provider settings are read at import time. The database tests point the
app at a broken database file.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent

GOOD_ITINERARY = {
    "itinerary": [
        {
            "day": day,
            "title": f"Day {day}",
            "activities": [
                {"time": "09:00", "name": f"Morning {day}", "location": "Centre", "estimated_cost": 100},
                {"time": "13:00", "name": f"Afternoon {day}", "location": "Old town", "estimated_cost": 200},
                {"time": "19:00", "name": f"Evening {day}", "location": "Market", "estimated_cost": 300},
            ],
        }
        for day in range(1, 4)
    ]
}

TRIP_PAYLOAD = {
    "origin": "Mumbai",
    "destination": "Paris",
    "days": 3,
    "budget": 50000,
    "people": 2,
    "travel_date": "2026-12-01",
}


def _free_port():
    import socket

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _StubProvider(BaseHTTPRequestHandler):
    """A fake OpenAI-compatible endpoint that misbehaves on purpose."""

    mode = "good"

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)

        if self.mode == "http_500":
            self.send_response(500)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")
            return

        if self.mode == "auth_401":
            self.send_response(401)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")
            return

        if self.mode == "garbage":
            content = "Sorry, I can't help with that."
        elif self.mode == "empty":
            content = ""
        elif self.mode == "wrong_day_count":
            content = json.dumps({"itinerary": GOOD_ITINERARY["itinerary"][:1]})
        elif self.mode == "missing_fields":
            content = json.dumps({"itinerary": [{"day": 1, "title": "x", "activities": [{"time": "09:00"}]}]})
        else:
            content = json.dumps(GOOD_ITINERARY)

        payload = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def stub_provider(request):
    """Start a stub provider and yield its base URL.

    The behaviour is chosen with `request.param`, so a test can override it
    with `@pytest.mark.parametrize("stub_provider", ["mode"], indirect=True)`.
    """
    _StubProvider.mode = getattr(request, "param", "good")
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _StubProvider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}/v1"
    server.shutdown()


def _run_trip_creation(base_url, extra_env=None):
    """Create a trip in a fresh process so the provider config is applied."""
    env = {
        **os.environ,
        "LLM_API_KEY": "test-key",
        "LLM_BASE_URL": base_url,
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_TIMEOUT_SECONDS": "10",
    }
    if extra_env:
        env.update(extra_env)

    script = f"""
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
response = client.post('/api/trips', json={TRIP_PAYLOAD!r})
print('RESULT' + json.dumps({{'status': response.status_code, 'body': response.json()}}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(BACKEND_ROOT),
    )
    for line in result.stdout.splitlines():
        if line.startswith("RESULT"):
            return json.loads(line[len("RESULT"):])
    raise AssertionError(f"no result from subprocess:\n{result.stdout}\n{result.stderr}")


# --------------------------------------------------------------------------
# AI provider failures
# --------------------------------------------------------------------------
class TestAiProvider:
    def test_valid_json_gives_a_real_plan(self, stub_provider):
        out = _run_trip_creation(stub_provider)
        assert out["status"] == 200
        assert out["body"]["is_mock"] is False
        # Null fields are excluded from the response.
        assert out["body"].get("warning") is None
        assert len(out["body"]["itinerary"]) == 3

    @pytest.mark.parametrize(
        "stub_provider", ["garbage", "empty", "http_500", "auth_401"], indirect=True
    )
    def test_transport_failures_fall_back_to_the_sample_plan(self, stub_provider):
        out = _run_trip_creation(stub_provider)
        assert out["status"] == 200
        assert out["body"]["is_mock"] is True
        assert out["body"].get("warning")
        # The user still gets a usable plan.
        assert len(out["body"]["itinerary"]) == 3

    def test_an_unreachable_provider_falls_back(self):
        out = _run_trip_creation("http://127.0.0.1:9/v1")
        assert out["status"] == 200
        assert out["body"]["is_mock"] is True

    @pytest.mark.parametrize(
        "stub_provider", ["wrong_day_count", "missing_fields"], indirect=True
    )
    def test_a_schema_mismatch_is_rejected_with_502(self, stub_provider):
        out = _run_trip_creation(stub_provider)
        assert out["status"] == 502
        error = out["body"]["error"]
        assert error["code"] == "invalid_ai_output"
        assert error["details"]["issues"]

    def test_no_api_key_uses_the_sample_plan(self):
        env = {**os.environ, "LLM_API_KEY": "", "FORCE_MOCK_AI": "true"}
        script = """
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
response = client.post('/api/trips', json=%r)
print('RESULT' + json.dumps({'status': response.status_code, 'body': response.json()}))
""" % TRIP_PAYLOAD
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, env=env, cwd=str(BACKEND_ROOT),
        )
        out = json.loads([l for l in result.stdout.splitlines() if l.startswith("RESULT")][0][6:])
        assert out["status"] == 200
        assert out["body"]["is_mock"] is True


# --------------------------------------------------------------------------
# Database failures
# --------------------------------------------------------------------------
class TestDatabaseFailures:
    """Each test uses its own database file, so the real one is never touched."""

    def _run_in_process(self, db_path, script_body):
        """Run a snippet in a fresh process against the given database file."""
        env = {**os.environ, "TRIP_DB_PATH": str(db_path)}
        result = subprocess.run(
            [sys.executable, "-c", script_body],
            capture_output=True, text=True, env=env, cwd=str(BACKEND_ROOT),
        )
        for line in result.stdout.splitlines():
            if line.startswith("RESULT"):
                return json.loads(line[len("RESULT"):])
        raise AssertionError(f"no result:\n{result.stdout}\n{result.stderr}")

    def _create_trip_script(self):
        return """
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
response = client.post('/api/trips', json=%r)
print('RESULT' + json.dumps({'status': response.status_code, 'body': response.json()}))
""" % TRIP_PAYLOAD

    def test_a_corrupt_database_falls_back_to_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "corrupt.db"
            db_path.write_bytes(b"this is not a sqlite file" * 200)
            out = self._run_in_process(db_path, self._create_trip_script())
        assert out["status"] == 200
        assert out["body"]["itinerary"]
        # The user is told the trip was not saved.
        assert out["body"].get("warning")
        assert "not persisted" in out["body"]["warning"]

    def test_a_corrupt_database_does_not_crash_the_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "corrupt.db"
            db_path.write_bytes(b"still not sqlite" * 200)
            out = self._run_in_process(db_path, self._create_trip_script())
        assert out["status"] < 500

    def test_sqlite_rejects_a_corrupt_file_directly(self):
        # Confirms the corrupt file really is unusable, so the test above is real.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.db"
            path.write_bytes(b"not a database" * 50)
            connection = sqlite3.connect(path)
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute("select count(*) from trips").fetchone()
            connection.close()

    def test_a_locked_database_falls_back_to_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "locked.db"
            connection = sqlite3.connect(db_path, timeout=1)
            connection.execute(
                "CREATE TABLE trips (trip_id TEXT PRIMARY KEY, data TEXT, created_at TEXT, updated_at TEXT)"
            )
            connection.commit()
            connection.execute("BEGIN EXCLUSIVE")
            connection.execute("INSERT INTO trips VALUES ('lock-probe', '{}', 't', 't')")
            try:
                out = self._run_in_process(db_path, self._create_trip_script())
            finally:
                connection.rollback()
                connection.close()
        assert out["status"] == 200
        assert "not persisted" in out["body"]["warning"]

    def test_a_healthy_database_persists_across_processes(self):
        """The trip must survive a restart, which is the point of using SQLite."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "persisted.db"
            script = """
import json
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
created = client.post('/api/trips', json=%r).json()
read = client.get('/api/trips/' + created['trip_id'])
print('RESULT' + json.dumps({'status': read.status_code, 'body': read.json()}))
""" % TRIP_PAYLOAD
            # First process creates the trip.
            self._run_in_process(db_path, script)
            # A second process reads it back.
            out = self._run_in_process(db_path, script)
        assert out["status"] == 200
        assert out["body"]["destination"] == "Paris"
        assert len(out["body"]["itinerary"]) == 3
