import httpx
import pytest
import respx

from opsclient import (
    NewPost,
    OpsApiError,
    OpsClient,
    OpsConnectionError,
    OpsNotFoundError,
    OpsServerError,
    OpsValidationError,
    Post,
    User,
)
from tests.conftest import POST_JSON, USER_JSON

# ---- success ----


def test_list_returns_typed_users(mock_api: respx.MockRouter, client: OpsClient) -> None:
    mock_api.get("/users").respond(200, json=[USER_JSON])
    users = client.list(User, "/users")
    assert users == [User(id=1, name="Asha Rao", username="asha", email="asha@example.com")]


def test_get_returns_one_user(mock_api: respx.MockRouter, client: OpsClient) -> None:
    mock_api.get("/users/1").respond(200, json=USER_JSON)
    assert client.get(User, "/users/1").email == "asha@example.com"


def test_create_sends_api_field_names(mock_api: respx.MockRouter, client: OpsClient) -> None:
    route = mock_api.post("/posts").respond(201, json=POST_JSON)
    post = client.create(Post, "/posts", NewPost(user_id=1, title="Hello", body="First post"))
    assert post.id == 101
    assert b'"userId":1' in route.calls.last.request.content  # sent as userId, not user_id


# ---- 404 and other client errors: never retried ----


def test_404_raises_not_found_without_retry(mock_api: respx.MockRouter, client: OpsClient) -> None:
    route = mock_api.get("/users/999").respond(404)
    with pytest.raises(OpsNotFoundError) as caught:
        client.get(User, "/users/999")
    assert caught.value.status_code == 404
    assert route.call_count == 1


@pytest.mark.parametrize("status", [400, 401, 403, 422])
def test_4xx_raises_api_error_without_retry(
    mock_api: respx.MockRouter, client: OpsClient, status: int
) -> None:
    route = mock_api.get("/users").respond(status)
    with pytest.raises(OpsApiError) as caught:
        client.list(User, "/users")
    assert caught.value.status_code == status
    assert route.call_count == 1


# ---- 500: retried ----


def test_500_then_success_is_retried(mock_api: respx.MockRouter, client: OpsClient) -> None:
    route = mock_api.get("/users").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(503),
            httpx.Response(200, json=[USER_JSON]),
        ]
    )
    assert len(client.list(User, "/users")) == 1
    assert route.call_count == 3


def test_500_every_time_gives_up_after_max_attempts(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    route = mock_api.get("/users").respond(500)
    with pytest.raises(OpsServerError):
        client.list(User, "/users")
    assert route.call_count == 3


def test_post_is_not_retried_on_500(mock_api: respx.MockRouter, client: OpsClient) -> None:
    route = mock_api.post("/posts").respond(500)
    with pytest.raises(OpsServerError):
        client.create(Post, "/posts", NewPost(user_id=1, title="Hello", body="x"))
    assert route.call_count == 1  # a second POST could create a duplicate


# ---- timeout and network failure: retried ----


def test_timeout_then_success_is_retried(mock_api: respx.MockRouter, client: OpsClient) -> None:
    route = mock_api.get("/users").mock(
        side_effect=[httpx.ReadTimeout("too slow"), httpx.Response(200, json=[USER_JSON])]
    )
    assert len(client.list(User, "/users")) == 1
    assert route.call_count == 2


def test_timeout_every_time_raises_connection_error(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    route = mock_api.get("/users").mock(side_effect=httpx.ConnectTimeout("too slow"))
    with pytest.raises(OpsConnectionError, match="timed out"):
        client.list(User, "/users")
    assert route.call_count == 3


def test_network_down_raises_connection_error(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    mock_api.get("/users").mock(side_effect=httpx.ConnectError("no route"))
    with pytest.raises(OpsConnectionError, match="could not reach"):
        client.list(User, "/users")


# ---- bad data ----


def test_missing_field_raises_validation_error(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    mock_api.get("/users/1").respond(200, json={"id": 1, "name": "No email"})
    with pytest.raises(OpsValidationError):
        client.get(User, "/users/1")


def test_list_endpoint_returning_object_raises(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    mock_api.get("/users").respond(200, json=USER_JSON)
    with pytest.raises(OpsValidationError, match="did not return a list"):
        client.list(User, "/users")


def test_non_json_body_raises_validation_error(
    mock_api: respx.MockRouter, client: OpsClient
) -> None:
    mock_api.get("/users").respond(200, text="<html>maintenance</html>")
    with pytest.raises(OpsValidationError, match="did not return JSON"):
        client.list(User, "/users")
