"""Tests for joppylib.api_client — Item CRUD, pagination, field validation"""

import pytest
import responses

from joppylib.api_client import Note, Tag, Folder, Item
from joppylib.config import Settings
from conftest import make_paginated_response


# ---------------------------------------------------------------------------
# Fixtures local to this module
# ---------------------------------------------------------------------------

@pytest.fixture
def note():
    return Note()


@pytest.fixture
def tag():
    return Tag()


@pytest.fixture
def folder():
    return Folder()


# ---------------------------------------------------------------------------
# fields_to_params
# ---------------------------------------------------------------------------

class TestFieldsToParams:

    def test_valid_fields(self, note):
        result = note.fields_to_params(["id", "title"])
        assert result == "id,title"

    def test_invalid_field_raises(self, note):
        with pytest.raises(ValueError, match="not_a_field is not an allowed field"):
            note.fields_to_params(["not_a_field"])

    def test_check_disabled(self, note):
        result = note.fields_to_params(["anything"], check=False)
        assert result == "anything"


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:

    @responses.activate
    def test_get_by_id(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes/note123?token={api_key}"
        responses.get(url, json={"id": "note123", "title": "Hello"})

        resp = note.get(api_key, settings, "note123")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Hello"

    @responses.activate
    def test_get_with_fields(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes/note123?token={api_key}&fields=id,title"
        responses.get(url, json={"id": "note123", "title": "Hello"})

        resp = note.get(api_key, settings, "note123", fields=["id", "title"])
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:

    @responses.activate
    def test_create_with_dict(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes?token={api_key}"
        responses.post(url, json={"id": "new1"}, status=200)

        data = {"title": "New", "body": "Content", "parent_id": "folder1"}
        resp = note.create(api_key, settings, data)
        assert resp.status_code == 200

    def test_create_missing_required_field(self, note, settings, api_key):
        with pytest.raises(ValueError, match="Required field body"):
            note.create(api_key, settings, {"title": "No body"})

    @responses.activate
    def test_create_with_string(self, tag, settings, api_key, base_url):
        url = f"{base_url}/tags?token={api_key}"
        responses.post(url, json={"id": "tag1", "title": "mytag"}, status=200)

        resp = tag.create(api_key, settings, "mytag")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:

    @responses.activate
    def test_update(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes/note123?token={api_key}"
        responses.put(url, json={"id": "note123"}, status=200)

        resp = note.update(api_key, settings, "note123", {"title": "Updated"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:

    @responses.activate
    def test_delete_to_trash(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes/note123?token={api_key}"
        responses.delete(url, status=200)

        resp = note.delete(api_key, settings, "note123", trash=True)
        assert resp.status_code == 200

    @responses.activate
    def test_delete_permanent(self, note, settings, api_key, base_url):
        url = f"{base_url}/notes/note123?token={api_key}&permanent=1"
        responses.delete(url, status=200)

        resp = note.delete(api_key, settings, "note123", trash=False)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# search — pagination
# ---------------------------------------------------------------------------

class TestSearch:

    @responses.activate
    def test_single_page(self, note, settings, api_key, base_url):
        items = [{"id": "1", "title": "A"}]
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response(items, has_more=False),
        )

        result = note.search(api_key, settings, "my query")
        assert result["success"] is True
        assert result["data"] == items

    @responses.activate
    def test_multi_page(self, note, settings, api_key, base_url):
        page1 = [{"id": "1"}]
        page2 = [{"id": "2"}]
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response(page1, has_more=True),
        )
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response(page2, has_more=False),
        )

        result = note.search(api_key, settings, "test")
        assert result["success"] is True
        assert len(result["data"]) == 2

    @responses.activate
    def test_failed_page(self, note, settings, api_key, base_url):
        responses.get(f"{base_url}/search", status=500)

        result = note.search(api_key, settings, "test")
        assert result["success"] is False
        assert "error" in result

    @responses.activate
    def test_non_note_type_param(self, tag, settings, api_key, base_url):
        """Non-note searches should include &type= in the URL."""
        items = [{"id": "t1", "title": "tag1"}]
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response(items, has_more=False),
        )

        result = tag.search(api_key, settings, "tag1")
        assert result["success"] is True
        # Verify the request included type=tag
        assert "type=tag" in responses.calls[0].request.url

    def test_invalid_order_by(self, note, settings, api_key):
        with pytest.raises(ValueError, match="not a valid field"):
            note.search(api_key, settings, "q", order_by="nonexistent")

    def test_invalid_order_dir(self, note, settings, api_key):
        with pytest.raises(ValueError, match="not valid"):
            note.search(api_key, settings, "q", order_dir="SIDEWAYS")

    @responses.activate
    def test_debug_includes_responses(self, note, settings, api_key, base_url):
        responses.get(
            f"{base_url}/search",
            json=make_paginated_response([], has_more=False),
        )

        result = note.search(api_key, settings, "q", debug=True)
        assert "responses" in result
        assert len(result["responses"]) == 1


# ---------------------------------------------------------------------------
# get_multi — pagination
# ---------------------------------------------------------------------------

class TestGetMulti:

    @responses.activate
    def test_single_page(self, note, settings, api_key, base_url):
        items = [{"id": "1"}, {"id": "2"}]
        responses.get(
            f"{base_url}/notes",
            json=make_paginated_response(items, has_more=False),
        )

        result = note.get_multi(api_key, settings)
        assert result["success"] is True
        assert result["data"] == items

    @responses.activate
    def test_multi_page(self, note, settings, api_key, base_url):
        responses.get(
            f"{base_url}/notes",
            json=make_paginated_response([{"id": "1"}], has_more=True),
        )
        responses.get(
            f"{base_url}/notes",
            json=make_paginated_response([{"id": "2"}], has_more=False),
        )

        result = note.get_multi(api_key, settings)
        assert result["success"] is True
        assert len(result["data"]) == 2

    @responses.activate
    def test_failed_request(self, note, settings, api_key, base_url):
        responses.get(f"{base_url}/notes", status=500)

        result = note.get_multi(api_key, settings)
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Note.get_all_tags
# ---------------------------------------------------------------------------

class TestNoteGetAllTags:

    @responses.activate
    def test_single_page(self, note, settings, api_key, base_url):
        tags = [{"id": "t1", "title": "urgent"}]
        responses.get(
            f"{base_url}/notes/note123/tags",
            json=make_paginated_response(tags, has_more=False),
        )

        result = note.get_all_tags(api_key, settings, "note123")
        assert result["success"] is True
        assert result["data"] == tags

    @responses.activate
    def test_multi_page(self, note, settings, api_key, base_url):
        responses.get(
            f"{base_url}/notes/note123/tags",
            json=make_paginated_response([{"id": "t1"}], has_more=True),
        )
        responses.get(
            f"{base_url}/notes/note123/tags",
            json=make_paginated_response([{"id": "t2"}], has_more=False),
        )

        result = note.get_all_tags(api_key, settings, "note123")
        assert result["success"] is True
        assert len(result["data"]) == 2


# ---------------------------------------------------------------------------
# Tag — add_to_note / remove_from_note
# ---------------------------------------------------------------------------

class TestTagNoteMethods:

    @responses.activate
    def test_add_to_note(self, tag, settings, api_key, base_url):
        url = f"{base_url}/tags/tag1/notes?token={api_key}"
        responses.post(url, json={"id": "note1"}, status=200)

        resp = tag.add_to_note(api_key, settings, "tag1", "note1")
        assert resp.status_code == 200
        # Verify the payload contained the note id
        import json
        assert json.loads(responses.calls[0].request.body) == {"id": "note1"}

    @responses.activate
    def test_remove_from_note(self, tag, settings, api_key, base_url):
        url = f"{base_url}/tags/tag1/notes/note1?token={api_key}"
        responses.delete(url, status=200)

        resp = tag.remove_from_note(api_key, settings, "tag1", "note1")
        assert resp.status_code == 200
