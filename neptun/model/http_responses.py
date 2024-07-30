from typing import List, Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    email: str = Field(..., alias='primary_email')

    def to_json(self):
        return self.dict(by_alias=True)


class SignUpHttpResponse(BaseModel):
    user: User = Field(..., alias='user')
    session_cookie: str = None
    logged_in_at: str = Field(..., alias='loggedInAt')

    def to_json(self):
        return self.dict(by_alias=True)


class LoginHttpResponse(BaseModel):
    user: User = Field(..., alias='user')
    session_cookie: str = None
    logged_in_at: str = Field(..., alias='loggedInAt')

    def to_json(self):
        return self.dict(by_alias=True)


class Issue(BaseModel):
    code: str
    message: str
    path: List[str]


class ErrorResponseData(BaseModel):
    issues: List[Issue]
    name: str


class ErrorResponse(BaseModel):
    statusCode: int
    statusMessage: str
    stack: List[str] = Field(default_factory=list)
    data: Optional[ErrorResponseData] = None


class Chat(BaseModel):
    id: int
    name: str
    model: str
    created_at: str
    updated_at: str
    chat_user_id: Optional[int]


class ChatsHttpResponse(BaseModel):
    chats: Optional[List[Chat]]


class GeneralErrorResponse(BaseModel):
    statusCode: int
    statusMessage: str


class CreateChatHttpResponse(BaseModel):
    chat: Chat
