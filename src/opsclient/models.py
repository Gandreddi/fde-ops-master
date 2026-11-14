"""Pydantic models: the shape of the data the API sends and accepts."""

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")  # the API sends more fields; we keep these

    id: int
    name: str
    username: str
    email: str


class Post(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: int = Field(alias="userId")  # JSON says userId, Python says user_id
    title: str
    body: str


class NewPost(BaseModel):
    """What you send to create a post (the server chooses the id)."""

    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId", gt=0)
    title: str = Field(min_length=1)
    body: str
