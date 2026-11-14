"""OpsClient: get one item, list many, create one. Every answer is checked by a Pydantic model."""

from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import BaseModel, ValidationError

from opsclient.errors import (
    OpsApiError,
    OpsConnectionError,
    OpsNotFoundError,
    OpsValidationError,
)

DEFAULT_BASE_URL = "https://jsonplaceholder.typicode.com"


class OpsClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        http: httpx.Client | None = None,
    ) -> None:
        # Passing in `http` lets tests use a fake transport instead of the real network.
        self._http = http or httpx.Client(base_url=base_url, timeout=timeout)

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

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        try:
            response = self._http.request(method, path, json=json)
        except httpx.TimeoutException as exc:
            raise OpsConnectionError(f"timed out calling {method} {path}") from exc
        except httpx.TransportError as exc:
            raise OpsConnectionError(f"could not reach the server: {exc}") from exc
        if response.status_code == 404:
            raise OpsNotFoundError(404, f"{path} was not found")
        if response.status_code >= 400:
            raise OpsApiError(response.status_code, response.text[:200])
        try:
            return response.json()
        except ValueError as exc:
            raise OpsValidationError(f"{path} did not return JSON") from exc

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
