# JopPyLib Testing Guide

Project-specific guide for running and extending the test suite.

---

## Running Tests

```bash
# Run the full suite
uv run pytest

# Verbose — see every test name and result
uv run pytest -v

# Run a specific test module
uv run pytest tests/test_api_client.py

# Run a single test class or test
uv run pytest tests/test_api_client.py::TestSearch
uv run pytest tests/test_api_client.py::TestSearch::test_multi_page

# Stop on first failure (useful when debugging)
uv run pytest -x
```

---

## Test Structure

```
tests/
├── conftest.py            # Shared fixtures and helpers
├── test_config.py         # Settings defaults and computed fields
├── test_connection.py     # check_connection, get_auth_token
├── test_api_client.py     # Low-level CRUD, pagination, field validation
└── test_joplin_client.py  # High-level client init and delegation
```

Each test file mirrors a source module:

| Source | Tests |
|--------|-------|
| `src/joppylib/config.py` | `tests/test_config.py` |
| `src/joppylib/connection.py` | `tests/test_connection.py` |
| `src/joppylib/api_client.py` | `tests/test_api_client.py` |
| `src/joppylib/joplin_client.py` | `tests/test_joplin_client.py` |

---

## Shared Fixtures (conftest.py)

Available to all test files automatically:

| Fixture | Type | Description |
|---------|------|-------------|
| `settings` | `Settings` | Default JopPyLib settings |
| `api_key` | `str` | Dummy API key: `"test_api_key_abc123"` |
| `base_url` | `str` | `"http://localhost:41184"` |

Helper function (import manually):

| Function | Description |
|----------|-------------|
| `make_paginated_response(items, has_more)` | Build a Joplin pagination response dict |

---

## How HTTP Mocking Works in This Project

All tests use the `responses` library to intercept `requests` calls. No test hits a real Joplin instance.

### Pattern: Simple request/response

```python
@responses.activate
def test_get_note(self, note, settings, api_key, base_url):
    # Register the fake response
    url = f"{base_url}/notes/note123?token={api_key}"
    responses.get(url, json={"id": "note123", "title": "Hello"})

    # Call the real code
    resp = note.get(api_key, settings, "note123")

    # Check the result
    assert resp.status_code == 200
    assert resp.json()["title"] == "Hello"
```

### Pattern: Paginated responses

Register multiple responses for the same base URL — consumed in order:

```python
@responses.activate
def test_multi_page(self, note, settings, api_key, base_url):
    responses.get(f"{base_url}/notes",
        json=make_paginated_response([{"id": "1"}], has_more=True))
    responses.get(f"{base_url}/notes",
        json=make_paginated_response([{"id": "2"}], has_more=False))

    result = note.get_multi(api_key, settings)
    assert len(result["data"]) == 2
```

### Pattern: Error responses

```python
responses.get(url, status=500)                           # HTTP error
responses.get(url, body=ConnectionError("refused"))      # Network error
```

---

## Adding New Tests

### Adding tests for an existing module

1. Open the corresponding `test_*.py` file
2. Find or create a `Test*` class for the feature area
3. Add a `test_*` method
4. Use `@responses.activate` if HTTP calls are involved
5. Run `uv run pytest -v` to verify

### Adding tests for a new module

1. Create `tests/test_newmodule.py`
2. Import what you need from the source and from `conftest`
3. Add shared fixtures to `conftest.py` if needed
4. Pytest auto-discovers the new file — no registration needed

### Checklist for a good test

- [ ] Named descriptively (`test_returns_false_on_500`, not `test_2`)
- [ ] Tests one behavior
- [ ] Independent — doesn't rely on other tests running first
- [ ] Uses `@responses.activate` if any HTTP calls are made
- [ ] Cleans up after itself (fixtures handle this automatically)
