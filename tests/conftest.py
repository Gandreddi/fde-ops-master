"""Shared test helpers. pytest finds fixtures in this file automatically."""

from collections.abc import Iterator

import pytest
import respx

from opsclient import OpsClient

BASE_URL = "https://api.test"

USER_JSON = {
    "id": 1,
    "name": "Asha Rao",
    "username": "asha",
    "email": "asha@example.com",
    "phone": "000",  # extra field: the model should ignore it
}
POST_JSON = {"id": 101, "userId": 1, "title": "Hello", "body": "First post"}


@pytest.fixture
def mock_api() -> Iterator[respx.MockRouter]:
    """A fake API. No test ever touches the real internet."""
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client() -> Iterator[OpsClient]:
    """A client with no waiting between retries, so tests stay fast."""
    with OpsClient(base_url=BASE_URL, max_attempts=3, backoff_seconds=0) as ops:
        yield ops
