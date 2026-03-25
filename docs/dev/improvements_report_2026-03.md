# JopPyLib — Critical Examination Report
**Date:** 2026-03-24
**Scope:** All source code in `src/joppylib/`
**Context:** All API traffic targets the Joplin Data API running on the user's localhost. Joplin Server is out-of-scope.

---

## 1. Input Sanitization

### No input sanitization on `query` in `search()` — Correctness bug
`api_client.py:107` interpolates the query directly into the URL string:
```python
params = f'?query={query}'
```
A query containing `&`, `=`, `#`, `+`, or spaces will break the URL or inject additional parameters. For example, searching for `C++` results in Joplin receiving `C  ` (plus decoded as space), and searching for `foo&limit=1` would override the pagination limit.

**Recommendation:** Use the `params` dict parameter of `requests.get()` instead of string concatenation. This handles URL encoding automatically and is the idiomatic Python approach. Joplin's server (Node.js `url.parse` with `querystring`) correctly decodes percent-encoded values.

---

## 2. Bugs & Correctness Issues

### Copy-paste docstring errors
- `delete()` docstring says "Get an entity instance by ID" (`api_client.py:385`, `joplin_client.py:246`).
- `update()` docstring says "data for the object to create" (`api_client.py:359`, `joplin_client.py:221`).

### `check_connection` ignores non-200 responses (`connection.py:30-33`)
```python
try:
    requests.get(url_ping)
    return True
except requests.exceptions.ConnectionError:
    return False
```
Any HTTP response (including 500) returns `True`. Only a connection failure returns `False`. A Joplin instance that is up but malfunctioning would be reported as connected.

### Inconsistent return types across methods
- `get()`, `create()`, `update()`, `delete()` return raw `requests.Response`.
- `search()`, `get_multi()`, `get_all_tags()` return `Dict[str, Any]` with a `success`/`data`/`error` wrapper.

Consumers must handle two completely different response patterns depending on which method they call.

### `name` class attribute collision in `joplin_client`
`joplin_client.Note` has class attribute `name: str = 'note'`, but its inherited `__init__` takes `name` as a parameter and overwrites it via `self.name = name`. The class attribute is dead code. Same for `Tag`.

### Unused `ITEM_TYPE` constant
`defaults.py` defines `ITEM_TYPE = 'note'` but it is never referenced anywhere in the codebase.

### Mutable default class attributes (`api_client.py:28-29`)
```python
fields: List[str] = []
fields_create_required: List[str] = []
```
Class-level mutable defaults. Not currently mutated, but a latent footgun if any code ever appends to them on an instance.

---

## 3. Robustness Issues

### Auth polling loop has no timeout and no delay (`connection.py:77-81`)
```python
while True:
    resp_check = requests.get(url_check)
    data_check = resp_check.json()
    if data_check['status'] != 'waiting':
        return data_check
```
Two problems:
1. If the user never responds to the Joplin auth dialog, this loops forever.
2. There is no `time.sleep()` between polls — it hammers the local Joplin API as fast as Python can loop, which can make the Joplin UI sluggish.

### `get_auth_token` doesn't handle HTTP errors (`connection.py:73-74`)
```python
resp_init = requests.post(url_init)
init_token = resp_init.json()['auth_token']
```
If the POST returns a non-200 or non-JSON response, this crashes with an unhelpful `KeyError` or `JSONDecodeError`.

### No timeout on any HTTP request
Every `requests.get/post/put/delete` call has no `timeout` parameter. If Joplin freezes (not uncommon for an Electron app under load), the calling Python code hangs indefinitely.

### No retry on paginated operations
If page 3 of 5 fails, the entire operation fails and all data (including successfully fetched pages 1-2) is discarded.

---

## 4. Design Issues

### Pagination loop duplicated 3 times
The same ~20-line pagination pattern is copy-pasted in `search()` (lines 131-157), `get_multi()` (lines 230-256), and `Note.get_all_tags()` (lines 513-539). They differ only in the initial URL. This has already caused bugs historically (per commits "Fixed: reponse indexes" and "Fixed: added req_index to fix indexing").

### The high-level layer is mostly boilerplate
Every method in `joplin_client.Item` is a pass-through that prepends `self._api_key` and `self.settings`. ~270 lines exist to hide two parameters. A `requests.Session`-style approach, `functools.partial`, or `__getattr__` delegation could achieve the same in a fraction of the code.

### No `requests.Session` usage
Every API call opens a new TCP connection. A `requests.Session` would provide connection reuse (faster for paginated calls that make many sequential requests), and a single place to configure timeouts and auth.

### `create()` accepts `Dict | str` but `str` bypasses validation (`api_client.py:331-338`)
When `data` is a string, required field validation is skipped entirely. The user gets a raw HTTP error with no library-level context if it fails.

### `JoplinClient` hard-codes entity specialization (`joplin_client.py:405-410`)
`folder`, `event`, `resource`, and `revision` use the base `Item` class. This means `resource` can't handle file uploads (per the TODO at `api_client.py:729`), and there's no way for a consumer to know this without reading the source.

### `id` shadows the Python builtin
Used as a parameter name throughout both layers. Convention is `item_id` or `id_`.

---

## 5. Testing & Quality

### Zero tests
This is the single biggest risk. The git history shows multiple pagination and indexing bugs that were caught manually. The triplicated pagination loop is especially prone to regressions.

### No CI/CD pipeline
No GitHub Actions, no linting, no type checking configured. The `py.typed` marker exists but `mypy`/`pyright` is not configured to run.

### `dist/` directory is checked into git
11 versions of wheels and tarballs bloat the repository. These should be built and published via CI or GitHub Releases.

---

## Summary

| Priority | Issue | Why it matters |
|----------|-------|----------------|
| **High** | No request timeouts | Hangs if Joplin freezes |
| **High** | Auth polling: no timeout, no delay | Infinite loop, pegs CPU, makes Joplin sluggish |
| **High** | URL query not encoded | Searches with special characters break silently |
| **High** | No tests | Every change risks regressions (proven by history) |
| **Medium** | Pagination loop duplicated 3x | Already caused bugs; will again |
| **Medium** | Inconsistent return types (Response vs Dict) | Confusing API for consumers |
| **Medium** | No `requests.Session` | Missed connection reuse, no central timeout config |
| **Medium** | `check_connection` ignores status codes | False positives |
| **Low** | Copy-paste docstring errors | Misleading docs |
| **Low** | `dist/` in git | Repository bloat |
| **Low** | Unused `ITEM_TYPE`, dead `name` class attrs | Dead code |
