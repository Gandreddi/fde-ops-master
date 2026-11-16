"""OpsClient: get one item, list many, create one. Every answer is checked by a Pydantic model.

Reads (GET) are retried with exponential backoff when the network fails or the server answers 5xx.
Writes (POST) are sent once, because sending one twice could create the same thing twice.
"""

import logging
import time
from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from opsclient.errors import (
    OpsApiError,
    OpsConnectionError,
    OpsNotFoundError,
    OpsServerError,
    OpsValidationError,
)

DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"
RETRYABLE = (OpsConnectionError, OpsServerError)

log = logging.getLogger("opsclient")


class OpsClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        http: httpx.Client | None = None,
    ) -> None:
        # Passing in `http` lets tests use a fake transport instead of the real network.
        self._http = http or httpx.Client(base_url=base_url, timeout=timeout)
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _send(self, method: str, path: str, json: dict[str, Any] | None) -> Any:
        """One attempt: send, then turn every kind of failure into one of our own errors."""
        started = time.perf_counter()
        try:
            response = self._http.request(method, path, json=json)
        except httpx.TimeoutException as exc:
            raise OpsConnectionError(f"timed out calling {method} {path}") from exc
        except httpx.TransportError as exc:
            raise OpsConnectionError(f"could not reach the server: {exc}") from exc
        log.info(
            "request finished",
            extra={
                "method": method,
                "path": path,
                "status": response.status_code,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        if response.status_code == 404:
            raise OpsNotFoundError(404, f"{path} was not found")
        if response.status_code >= 500:
            raise OpsServerError(response.status_code, response.text[:200])
        if response.status_code >= 400:
            raise OpsApiError(response.status_code, response.text[:200])
        try:
            return response.json()
        except ValueError as exc:
            raise OpsValidationError(f"{path} did not return JSON") from exc

    def _log_retry(self, state: RetryCallState) -> None:
        error = state.outcome.exception() if state.outcome else None
        log.warning(
            "request failed, retrying",
            extra={
                "attempt": state.attempt_number,
                "max_attempts": self._max_attempts,
                "error": str(error),
            },
        )

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        attempts = self._max_attempts if method == "GET" else 1
        retrying = Retrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=self._backoff_seconds, max=8),  # 0.5s, 1s, 2s, ...
            retry=retry_if_exception_type(RETRYABLE),
            before_sleep=self._log_retry,
            reraise=True,  # after the last attempt, raise our own error, not tenacity's
        )
        return retrying(self._send, method, path, json)

    def get[T: BaseModel](self, model: type[T], path: str) -> T:
        """Fetch one item and return it as `model`."""
        data = self._request("GET", path)
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise OpsValidationError(f"unexpected data from {path}: {exc}") from exc

    def list[T: BaseModel](self, model: type[T], path: str) -> "list[T]":
        """Fetch many items and return them as a list of `model`."""
        data = self._request("GET", path)
        if not isinstance(data, list):
            raise OpsValidationError(f"{path} did not return a list")
        try:
            return [model.model_validate(item) for item in data]
        except ValidationError as exc:
            raise OpsValidationError(f"unexpected data from {path}: {exc}") from exc

    def create[T: BaseModel](self, model: type[T], path: str, payload: BaseModel) -> T:
        """Send `payload` and return what the server created, as `model`."""
        data = self._request("POST", path, json=payload.model_dump(by_alias=True))
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise OpsValidationError(f"unexpected data from {path}: {exc}") from exc
