# Understanding Software Testing

A practical guide to testing concepts, using JopPyLib (a Python wrapper for the Joplin API) as a running example.

---

## Why Test?

Testing is writing code that verifies your other code works correctly. But the real benefits go deeper than "catching bugs":

1. **Confidence to change things.** Without tests, every change is a gamble. With tests, you refactor freely — if the tests still pass, you didn't break anything.

2. **Documentation that runs.** Tests show exactly how your code is supposed to behave. Unlike comments, tests can't go stale — they fail when they become wrong.

3. **Catching regressions.** A regression is when something that used to work stops working. JopPyLib's git history shows pagination bugs that were caught manually and fixed multiple times. Tests would have caught those regressions instantly.

4. **Faster feedback loops.** Running a test suite takes seconds. Manually testing by opening Joplin, creating notes, and checking results takes minutes. Over time, this compounds enormously.

---

## The Testing Pyramid

Not all tests are the same. They form a pyramid — more of the fast, cheap ones at the bottom, fewer of the slow, expensive ones at the top.

```
        /  E2E  \         Few — slow, brittle, but high confidence
       /----------\
      / Integration \     Some — test components working together
     /----------------\
    /    Unit Tests     \  Many — fast, isolated, easy to write
   /____________________\
```

### Unit Tests

Test a single function or method in isolation. Everything external (HTTP calls, databases, file system) is replaced with fakes.

**Example from JopPyLib:** Testing that `fields_to_params(["id", "title"])` returns `"id,title"`, or that passing an invalid field raises `ValueError`. No HTTP calls needed — we're just testing string logic.

```python
def test_valid_fields():
    note = Note()
    result = note.fields_to_params(["id", "title"])
    assert result == "id,title"
```

### Integration Tests

Test that multiple components work together correctly. You might use a real database but mock external APIs, or test that your HTTP client correctly talks to a test server.

**Example from JopPyLib:** Testing that `JoplinClient.__init__` with `auth_method="interactive"` correctly calls `check_connection()`, then `get_auth_token()`, and wires up all the entity types. Multiple real components interact, but HTTP is still mocked.

### End-to-End (E2E) Tests

Test the entire system as a user would use it. For JopPyLib, this would mean running against a real Joplin instance — creating actual notes, searching them, deleting them. These are slow, require setup, and can be flaky, so you write fewer of them.

**For a library like JopPyLib:** Unit tests and integration tests give you the best return on investment. E2E tests against a real Joplin instance are useful but optional — you'd run them manually or in a special CI environment.

---

## Key Vocabulary

| Term | What It Means |
|------|--------------|
| **Test case** | A single test: one scenario, one expected outcome. In pytest, it's a function starting with `test_`. |
| **Test suite** | All your tests together. Running `pytest` runs the full suite. |
| **Assertion** | A statement that something must be true. `assert result == "id,title"` — if it's false, the test fails. |
| **Fixture** | Reusable setup code. Instead of creating a `Settings()` object in every test, you define it once as a fixture and pytest injects it automatically. |
| **Mock** | A fake object that replaces something real. When testing HTTP code, you mock the HTTP calls so they don't actually hit a server. |
| **Stub** | Similar to a mock, but simpler — just returns a fixed value. A mock can also verify it was called correctly. |
| **Coverage** | The percentage of your code that gets executed during tests. 80% coverage means 20% of your code has no tests touching it. |
| **Regression** | A bug where something that previously worked breaks. Tests that catch regressions are called regression tests. |
| **Parametrize** | Running the same test with different inputs. Instead of writing 5 nearly identical tests, you write one and feed it 5 sets of data. |

---

## What Is Mocking and Why Do You Need It?

Consider testing this JopPyLib function:

```python
def check_connection(base_url, route_ping):
    url_ping = f'{base_url}/{route_ping}'
    try:
        resp = requests.get(url_ping, timeout=(3, 5))
        return resp.ok
    except requests.exceptions.RequestException:
        return False
```

If you test this without mocking, your test would:
- Need a running Joplin instance
- Fail if Joplin isn't running
- Be slow (real HTTP is slow compared to function calls)
- Be unpredictable (network issues, Joplin state)

**Mocking replaces the real HTTP call with a fake one that you control.** You tell the mock: "When someone makes a GET to this URL, return this response." The test runs in milliseconds, needs no external services, and is perfectly reproducible.

```python
@responses.activate  # This decorator activates HTTP mocking
def test_returns_true_on_200():
    # Arrange: set up the fake response
    responses.get("http://localhost:41184/ping", body="JoplinClipperServer")

    # Act: call the real function — it hits the mock, not the network
    result = check_connection()

    # Assert: verify the result
    assert result is True
```

The `responses` library also **blocks real HTTP calls** by default. If your code accidentally tries to make a real request during a test, it will fail loudly instead of silently hitting the network. This is a safety net.

### When NOT to mock

Don't mock the thing you're testing. If you're testing `check_connection`, mock the HTTP layer beneath it, not `check_connection` itself. Mock the *dependencies*, not the *subject*.

---

## Anatomy of a Test: Arrange / Act / Assert

Every well-structured test follows three steps, often called **AAA** (or "triple-A"):

```python
def test_create_missing_required_field():
    # ARRANGE — set up the objects and data you need
    note = Note()
    settings = Settings()
    api_key = "test_key"

    # ACT + ASSERT — call the code and verify the outcome
    # (For exceptions, pytest.raises combines both steps)
    with pytest.raises(ValueError, match="Required field body"):
        note.create(api_key, settings, {"title": "No body"})
```

**Arrange:** Create the objects, prepare the inputs, set up mocks. This is the "given" — given this starting state...

**Act:** Call the function or method you're testing. This is the "when" — when I do this...

**Assert:** Check that the result matches your expectation. This is the "then" — then this should happen.

Sometimes Arrange is handled by fixtures (shared setup), and sometimes Act and Assert are combined (like with `pytest.raises`). That's fine — the mental model still applies.

---

## What Makes a Good Test?

### Good tests are:

**1. Independent.** Each test runs on its own. Test A doesn't depend on Test B running first. If you need shared state, use fixtures — pytest creates fresh ones for each test.

**2. Readable.** A test is documentation. Someone (including future you) should be able to read a test and understand what behavior it verifies. Name your tests clearly:
- `test_returns_true_on_200` — yes, says exactly what it checks
- `test_connection_1` — no, says nothing about what's being tested

**3. Focused.** One test, one behavior. Don't assert 10 different things in one test. If it fails, you want to know exactly what broke.

**4. Fast.** Your entire test suite should run in seconds, not minutes. This means mocking external dependencies. If tests are slow, developers stop running them.

**5. Deterministic.** Same code = same result, every time. No randomness, no dependency on current time, no relying on network availability.

### Bad tests:

**Testing implementation details.** Don't test *how* something works internally — test *what* it produces. If you refactor the internals without changing behavior, tests shouldn't break.

```python
# BAD: tests internal implementation
def test_search_builds_url_with_ampersand_between_params():
    ...

# GOOD: tests observable behavior
def test_search_returns_matching_items():
    ...
```

**Testing the framework.** Don't test that `requests.get` works or that Python's `json.loads` parses JSON. Those are someone else's responsibility.

**Tautological tests.** Don't test that the code does what the code does:

```python
# BAD: just restating the implementation
def test_base_url():
    s = Settings()
    assert s.base_url == f"{s.protocol}{s.host}:{s.port}"

# GOOD: testing against a known expected value
def test_base_url():
    s = Settings()
    assert s.base_url == "http://localhost:41184"
```

---

## When NOT to Test

Testing has diminishing returns. Focus your energy where it matters most:

1. **Don't test trivial code.** A one-line property that returns a string? Probably not worth a dedicated test unless it does computation (like `base_url`).

2. **Don't test third-party code.** You don't need to verify that `requests.get` works or that `pydantic` validates correctly.

3. **Don't aim for 100% coverage.** Chasing the last 5% of coverage often means writing brittle tests for error paths that are nearly impossible to trigger. 70-80% coverage of meaningful code is usually a better target than 100% coverage of everything.

4. **Don't test pure delegation.** In JopPyLib, the `joplin_client.Item.get()` method just calls `self._api_client.get()` with two extra parameters. A few spot-checks that delegation works are fine — exhaustive testing of every delegation method is redundant with the `api_client` tests.

---

## The Feedback Loop

The real power of testing shows up over time:

```
Write code → Write tests → Tests pass → Ship it
                                ↓
                Change code → Run tests → Tests fail?
                                            ↓
                                    Fix the regression
                                            ↓
                                    Tests pass → Ship it
```

Every time you (or someone else) changes JopPyLib — fixing a bug, adding a feature, refactoring — the test suite catches anything that breaks. The more tests you have, the more confidently you can change things. That's the real payoff: **tests buy you the freedom to evolve your code.**
