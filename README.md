# fde-ops-copilot

`opsclient`: a small typed Python SDK and CLI for a REST API (JSONPlaceholder), with retries,
structured logs and tests.

## Install and run

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync                 # create .venv and install everything from uv.lock
uv run ops list-users   # print the users from the API
uv run pytest -v        # run the tests (no internet needed)
uv run mypy             # type check (strict)
uv run ruff check .     # lint
```

Use it from Python:

```python
from opsclient import NewPost, OpsClient, Post, User

with OpsClient() as client:
    user = client.get(User, "/users/1")
    posts = client.list(Post, "/posts")
    created = client.create(Post, "/posts", NewPost(user_id=1, title="Hello", body="First post"))
```

## Settings

Set these as environment variables, or put them in a `.env` file (never commit it).

| Variable | Default | Meaning |
|---|---|---|
| `OPS_BASE_URL` | `https://jsonplaceholder.typicode.com` | API address |
| `OPS_TIMEOUT_SECONDS` | `10` | How long to wait for one answer |
| `OPS_MAX_ATTEMPTS` | `3` | Tries for a GET before giving up |
| `OPS_LOG_LEVEL` | `WARNING` | Use `INFO` to see one JSON log line per request |

## Retries

GET requests are retried on timeouts, network errors and 5xx answers, waiting 0.5s, 1s, 2s...
between tries. 4xx answers and POST requests are never retried.

## Layout

- `src/opsclient/models.py`: Pydantic models (`User`, `Post`, `NewPost`)
- `src/opsclient/client.py`: `OpsClient` with `get`, `list`, `create`
- `src/opsclient/errors.py`: `OpsClientError` and its subclasses
- `src/opsclient/cli.py`: the `ops` command
- `src/opsclient/settings.py`: settings from `OPS_*` environment variables
- `src/opsclient/logging_config.py`: JSON log formatter
- `tests/`: pytest tests with a mocked API (respx)
- `.github/workflows/ci.yml`: runs ruff, mypy and pytest on every push and pull request
