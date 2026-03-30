# Python Testing Setup — Step by Step

How to add pytest-based testing to a new or existing Python project. Covers pytest basics, fixtures, mocking HTTP with `responses`, and parametrize.

---

## 1. Install pytest

If you use **uv** (recommended):

```bash
# Add pytest as a dev dependency (not shipped with your package)
uv add --dev pytest
```

If you use **pip**:

```bash
pip install pytest
```

## 2. Configure pytest in pyproject.toml

Add this section to your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

This tells pytest to look for tests in the `tests/` directory. Without it, pytest scans the entire project, which is slower and can pick up unintended files.

## 3. Create the test directory

```
your_project/
├── src/
│   └── your_package/
├── tests/
│   ├── conftest.py      # Shared fixtures (optional but recommended)
│   ├── test_module_a.py
│   └── test_module_b.py
└── pyproject.toml
```

**Naming conventions** (pytest auto-discovers these):
- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*`
- Test classes: `Test*` (no `__init__`)

## 4. Write your first test

```python
# tests/test_example.py

def test_addition():
    assert 1 + 1 == 2

def test_string_upper():
    assert "hello".upper() == "HELLO"
```

Run it:

```bash
uv run pytest       # Basic run
uv run pytest -v    # Verbose — shows each test name
```

## 5. Run tests

```bash
# Run all tests
uv run pytest

# Verbose output (see each test name and result)
uv run pytest -v

# Run a specific file
uv run pytest tests/test_module_a.py

# Run a specific test class
uv run pytest tests/test_module_a.py::TestClassName

# Run a specific test
uv run pytest tests/test_module_a.py::TestClassName::test_method_name

# Stop on first failure
uv run pytest -x

# Show print() output (normally captured)
uv run pytest -s
```

---

## Fixtures

Fixtures provide reusable setup for your tests. Instead of repeating the same object creation in every test, define it once.

### Basic fixture

```python
# tests/conftest.py — fixtures here are available to ALL test files

import pytest
from mypackage.config import Settings

@pytest.fixture
def settings():
    """A Settings instance with defaults."""
    return Settings()
```

```python
# tests/test_something.py

def test_base_url(settings):  # pytest sees the parameter name, finds the fixture
    assert settings.base_url == "http://localhost:41184"
```

**How it works:** When pytest sees a test function parameter that matches a fixture name, it automatically calls the fixture and passes the result. Each test gets a fresh instance — fixtures are recreated for every test by default.

### Fixture in conftest.py vs in the test file

- `conftest.py` — fixtures available to **all** test files in the same directory (and subdirectories)
- Inside a test file — fixture available only to tests in **that file**

Put broadly-used fixtures (settings, database connections, API keys) in `conftest.py`. Put test-specific fixtures in the test file itself.

### Fixtures that depend on other fixtures

Fixtures can use other fixtures:

```python
@pytest.fixture
def settings():
    return Settings()

@pytest.fixture
def base_url(settings):  # This fixture uses the settings fixture
    return settings.base_url
```

---

## Mocking HTTP with `responses`

When your code makes HTTP calls (using the `requests` library), you don't want tests hitting real servers. The `responses` library intercepts `requests` calls and returns fake responses you define.

### Install

```bash
uv add --dev responses
```

### Basic usage

```python
import responses
from mypackage import check_connection

@responses.activate  # Decorator: activates mocking for this test
def test_connection_ok():
    # Register a fake response
    responses.get("http://localhost:41184/ping", body="OK", status=200)

    # Call your code — it hits the mock, not the real server
    result = check_connection()
    assert result is True
```

### What `@responses.activate` does

1. **Intercepts** all `requests.get/post/put/delete` calls
2. **Matches** them against your registered responses
3. **Returns** the fake response you defined
4. **Blocks** any unregistered URLs — if your code tries to hit a URL you didn't mock, the test fails with a `ConnectionError`. This prevents accidental real HTTP calls.

### Mocking different HTTP methods

```python
responses.get(url, json={"key": "value"})       # GET
responses.post(url, json={"id": "new"})          # POST
responses.put(url, status=200)                   # PUT
responses.delete(url, status=200)                # DELETE
```

### Mocking error responses

```python
responses.get(url, status=500)                              # Server error
responses.get(url, body=ConnectionError("refused"))         # Network error
```

### Mocking multiple calls to the same URL (pagination)

Register multiple responses for the same URL — they're consumed in order:

```python
@responses.activate
def test_pagination():
    # First call returns page 1
    responses.get("http://localhost:41184/notes", json={
        "items": [{"id": "1"}],
        "has_more": True
    })
    # Second call returns page 2
    responses.get("http://localhost:41184/notes", json={
        "items": [{"id": "2"}],
        "has_more": False
    })

    result = get_all_notes()
    assert len(result) == 2
```

### Inspecting what was sent

After the test runs, you can check what your code actually sent:

```python
@responses.activate
def test_payload():
    responses.post("http://example.com/api", json={"ok": True})

    my_function()  # Makes the POST call

    # Check what was sent
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "http://example.com/api"
    assert json.loads(responses.calls[0].request.body) == {"id": "note1"}
```

---

## Testing Exceptions

Use `pytest.raises` to verify that code raises the expected exception:

```python
import pytest

def test_missing_field_raises():
    with pytest.raises(ValueError, match="Required field"):
        create_note({"title": "no body"})
```

- `pytest.raises(ExceptionType)` — test passes only if that exception is raised
- `match="pattern"` — optional regex check on the error message

---

## Parametrize — One Test, Many Inputs

Instead of writing multiple nearly-identical tests:

```python
# Without parametrize — repetitive
def test_asc():
    validate_order_dir("ASC")  # should not raise

def test_desc():
    validate_order_dir("DESC")  # should not raise
```

Use `@pytest.mark.parametrize`:

```python
@pytest.mark.parametrize("direction", ["ASC", "DESC"])
def test_valid_order_dir(direction):
    validate_order_dir(direction)  # should not raise

@pytest.mark.parametrize("direction", ["SIDEWAYS", "up", ""])
def test_invalid_order_dir(direction):
    with pytest.raises(ValueError):
        validate_order_dir(direction)
```

Pytest runs the test once for each parameter value, reporting each as a separate result.

### Multiple parameters

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("Hello World", "HELLO WORLD"),
])
def test_upper(input, expected):
    assert input.upper() == expected
```

---

## Organizing Tests

### Test classes

Group related tests into classes. No `__init__` needed — pytest handles instantiation:

```python
class TestCheckConnection:

    @responses.activate
    def test_returns_true_on_200(self):
        responses.get("http://localhost:41184/ping", body="OK")
        assert check_connection() is True

    @responses.activate
    def test_returns_false_on_500(self):
        responses.get("http://localhost:41184/ping", status=500)
        assert check_connection() is False
```

### File organization

Mirror your source structure:

```
src/mypackage/config.py      →  tests/test_config.py
src/mypackage/connection.py   →  tests/test_connection.py
src/mypackage/api_client.py   →  tests/test_api_client.py
```

---

## Common Patterns and Gotchas

### Pattern: Helper functions in conftest.py

For reusable test utilities (not fixtures), define regular functions in `conftest.py`:

```python
# conftest.py
def make_paginated_response(items, has_more=False):
    return {"items": items, "has_more": has_more}
```

Import them in test files:

```python
from conftest import make_paginated_response
```

### Gotcha: Fixtures are recreated per test

Each test gets a **fresh** fixture instance. If test A modifies a fixture object, test B still gets the original. This is intentional — it keeps tests independent.

### Gotcha: `responses` only works with `requests`

If your code uses `httpx`, `aiohttp`, or `urllib`, `responses` won't intercept those calls. It only works with the `requests` library.

### Gotcha: Forgetting `@responses.activate`

Without the decorator, mocking isn't active and your code will attempt real HTTP calls (which will fail in most test environments).

### Gotcha: URL matching is exact

`responses.get("http://localhost:41184/notes")` matches any URL that **starts with** that string, so query parameters are automatically handled. But the scheme, host, port, and path must match exactly.

---

## Quick Reference

| What | Command / Code |
|------|---------------|
| Install pytest | `uv add --dev pytest` |
| Run all tests | `uv run pytest` |
| Run verbose | `uv run pytest -v` |
| Run one file | `uv run pytest tests/test_foo.py` |
| Run one test | `uv run pytest tests/test_foo.py::test_bar` |
| Stop on first failure | `uv run pytest -x` |
| Show print output | `uv run pytest -s` |
| Mock HTTP | `@responses.activate` + `responses.get(url, ...)` |
| Test exceptions | `with pytest.raises(ValueError, match="msg"):` |
| Parametrize | `@pytest.mark.parametrize("name", [val1, val2])` |
| Shared fixture | Define in `conftest.py` with `@pytest.fixture` |
