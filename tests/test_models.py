import pytest
from pydantic import ValidationError

from opsclient import NewPost, User


@pytest.mark.parametrize("field", ["username", "handle"])
def test_user_accepts_old_and_new_field_name(field: str) -> None:
    """The customer renamed username to handle; both must keep working."""
    user = User.model_validate({"id": 1, "name": "Asha Rao", field: "asha", "email": "a@x.io"})
    assert user.username == "asha"


def test_user_without_username_or_handle_is_rejected() -> None:
    with pytest.raises(ValidationError):
        User.model_validate({"id": 1, "name": "Asha Rao", "email": "a@x.io"})


def test_new_post_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        NewPost(user_id=1, title="", body="x")
