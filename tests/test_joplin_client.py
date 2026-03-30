"""Tests for joppylib.joplin_client — JoplinClient init and delegation"""

import pytest
import responses

from joppylib.joplin_client import JoplinClient, Item, Note, Tag
from joppylib.api_client import APIClient
from joppylib.config import Settings
from joppylib.exceptions import AuthorizationDeniedError
from conftest import make_paginated_response


# ---------------------------------------------------------------------------
# JoplinClient.__init__
# ---------------------------------------------------------------------------

class TestJoplinClientInit:

    def test_auth_key(self, settings):
        """auth_method='key' with a valid key should work."""
        client = JoplinClient(settings, auth_method="key", api_key="mykey")
        assert client._api_key == "mykey"

    def test_auth_key_missing_raises(self, settings):
        """auth_method='key' without api_key should raise ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            JoplinClient(settings, auth_method="key")

    def test_invalid_auth_method_raises(self, settings):
        with pytest.raises(ValueError, match="can be"):
            JoplinClient(settings, auth_method="magic")

    @responses.activate
    def test_auth_interactive_accepted(self, settings):
        """Interactive auth flow: ping OK, auth accepted."""
        base = settings.base_url
        responses.get(f"{base}/ping", body="JoplinClipperServer")
        responses.post(f"{base}/auth", json={"auth_token": "init"})
        responses.get(
            f"{base}/auth/check",
            json={"status": "accepted", "token": "real_key"},
        )

        client = JoplinClient(settings, auth_method="interactive")
        assert client._api_key == "real_key"

    @responses.activate
    def test_auth_interactive_denied(self, settings):
        """Interactive auth flow: user denies access."""
        base = settings.base_url
        responses.get(f"{base}/ping", body="JoplinClipperServer")
        responses.post(f"{base}/auth", json={"auth_token": "init"})
        responses.get(f"{base}/auth/check", json={"status": "rejected"})

        with pytest.raises(AuthorizationDeniedError):
            JoplinClient(settings, auth_method="interactive")

    def test_entity_types_available(self, settings):
        """After init, note/tag/folder/event/resource/revision are available."""
        client = JoplinClient(settings, auth_method="key", api_key="k")
        assert isinstance(client.note, Note)
        assert isinstance(client.tag, Tag)
        assert isinstance(client.folder, Item)
        assert isinstance(client.event, Item)
        assert isinstance(client.resource, Item)
        assert isinstance(client.revision, Item)


# ---------------------------------------------------------------------------
# Delegation — spot-check that high-level methods reach the API
# ---------------------------------------------------------------------------

class TestDelegation:

    @pytest.fixture
    def client(self, settings):
        return JoplinClient(settings, auth_method="key", api_key="testkey")

    @responses.activate
    def test_note_get(self, client, base_url):
        url = f"{base_url}/notes/n1?token=testkey"
        responses.get(url, json={"id": "n1", "title": "Hello"})

        resp = client.note.get("n1")
        assert resp.json()["title"] == "Hello"

    @responses.activate
    def test_note_search(self, client, base_url):
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response(
                [{"id": "n1"}], has_more=False
            ),
        )

        result = client.note.search("hello")
        assert result["success"] is True
        assert len(result["data"]) == 1

    @responses.activate
    def test_tag_add_to_note(self, client, base_url):
        url = f"{base_url}/tags/t1/notes?token=testkey"
        responses.post(url, json={"id": "n1"}, status=200)

        resp = client.tag.add_to_note("t1", "n1")
        assert resp.status_code == 200
