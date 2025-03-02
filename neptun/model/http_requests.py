import json
from typing import List, Optional
from pydantic import BaseModel, Field, RootModel
import httpx
from datetime import datetime


class SignUpHttpRequest(BaseModel):
    email: str = Field(serialization_alias="email")
    password: str
    confirmPassword: str


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


class UserFile(BaseModel):
    title: Optional[str]
    text: str
    language: str
    extension: str
    neptun_user_id: int


class TemplateData(BaseModel):
    description: Optional[str]
    file_name: str
    neptun_user_id: int


class Template(BaseModel):
    id: int
    description: Optional[str]
    file_name: str
    created_at: datetime
    updated_at: datetime
    neptun_user_id: int
    template_collection_id: Optional[int]
    user_file_id: Optional[int]


class CreateTemplateRequest(BaseModel):
    template: TemplateData
    file: UserFile


class CreateCollectionRequest(BaseModel):
    name: str
    description: Optional[str]
    is_shared: bool
    neptun_user_id: Optional[int]


class UpdateCollectionRequest(BaseModel):
    name: Optional[str]
    description: Optional[str]
    is_shared: Optional[bool]
    neptun_user_id: int


class UpdateChatRequest(BaseModel):
    name: str
    model: str


class CreateNeptunProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    main_language: str
    neptun_user_id: int

