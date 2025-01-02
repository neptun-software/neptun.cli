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


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message] = Field(serialization_alias="messages")


class ResetPasswordRequest(BaseModel):
    otp: str
    new_password: str


class OTPCreateRequest(BaseModel):
    action: str = "create"
    email: str


class OTPValidateRequest(BaseModel):
    action: str = "validate"
    email: str
    otp: str
    new_password: str





