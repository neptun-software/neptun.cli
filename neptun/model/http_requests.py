import json
from typing import List
from pydantic import BaseModel, Field, RootModel
import httpx


class SignUpHttpRequest(BaseModel):
    email: str = Field(serialization_alias="email")
    password: str


class LoginHttpRequest(BaseModel):
    email: str = Field(serialization_alias="email")
    password: str


class CreateChatHttpRequest(BaseModel):
    model: str
    name: str






