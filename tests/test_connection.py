"""Tests for joppylib.connection — check_connection and get_auth_token"""

import pytest
import responses
from requests.exceptions import ConnectionError

from joppylib.connection import check_connection, get_auth_token


# ---------------------------------------------------------------------------
# check_connection
# ---------------------------------------------------------------------------

class TestCheckConnection:

    @responses.activate
    def test_returns_true_on_200(self):
        responses.get("http://localhost:41184/ping", body="JoplinClipperServer")
        assert check_connection() is True

    @responses.activate
    def test_returns_false_on_500(self):
        responses.get("http://localhost:41184/ping", status=500)
        assert check_connection() is False

    @responses.activate
    def test_returns_false_on_connection_error(self):
        responses.get(
            "http://localhost:41184/ping",
            body=ConnectionError("refused"),
        )
        assert check_connection() is False

    @responses.activate
    def test_custom_url_and_route(self):
        responses.get("https://myhost:9999/health", body="ok")
        assert check_connection("https://myhost:9999", "health") is True


# ---------------------------------------------------------------------------
# get_auth_token
# ---------------------------------------------------------------------------

class TestGetAuthToken:

    @responses.activate
    def test_accepted(self):
        """User accepts the auth dialog on the first poll."""
        responses.post(
            "http://localhost:41184/auth",
            json={"auth_token": "init_tok"},
        )
        responses.get(
            "http://localhost:41184/auth/check",
            json={"status": "accepted", "token": "real_api_key"},
        )

        result = get_auth_token()
        assert result["status"] == "accepted"
        assert result["token"] == "real_api_key"

    @responses.activate
    def test_rejected(self):
        """User explicitly rejects the auth dialog."""
        responses.post(
            "http://localhost:41184/auth",
            json={"auth_token": "init_tok"},
        )
        responses.get(
            "http://localhost:41184/auth/check",
            json={"status": "rejected"},
        )

        result = get_auth_token()
        assert result["status"] == "rejected"

    @responses.activate
    def test_accepted_after_waiting(self):
        """User accepts after one 'waiting' poll cycle."""
        responses.post(
            "http://localhost:41184/auth",
            json={"auth_token": "init_tok"},
        )
        # First check: still waiting
        responses.get(
            "http://localhost:41184/auth/check",
            json={"status": "waiting"},
        )
        # Second check: accepted
        responses.get(
            "http://localhost:41184/auth/check",
            json={"status": "accepted", "token": "my_key"},
        )

        result = get_auth_token(poll_interval=0.01, poll_timeout=5.0)
        assert result["status"] == "accepted"
        assert result["token"] == "my_key"

    @responses.activate
    def test_timeout_raises(self):
        """If the user never responds, TimeoutError is raised."""
        responses.post(
            "http://localhost:41184/auth",
            json={"auth_token": "init_tok"},
        )
        # Always return waiting
        responses.get(
            "http://localhost:41184/auth/check",
            json={"status": "waiting"},
        )

        with pytest.raises(TimeoutError):
            get_auth_token(poll_interval=0.01, poll_timeout=0.05)
