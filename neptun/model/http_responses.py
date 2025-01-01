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
    neptun_user_id: Optional[int]


class ChatsHttpResponse(BaseModel):
    chats: Optional[List[Chat]]


class GeneralErrorResponse(BaseModel):
    statusCode: int
    statusMessage: str


class CreateChatHttpResponse(BaseModel):
    chat: Chat


class ChatMessage(BaseModel):
    id: int
    message: str
    actor: str
    created_at: str
    updated_at: str
    neptun_user_id: int
    chat_conversation_id: int


class ChatMessagesHttpResponse(BaseModel):
    chat_messages: List[ChatMessage] = Field(..., alias='chatMessages')


class Installation(BaseModel):
    github_repository_id: int
    github_repository_name: str
    github_repository_description: Optional[str] = None
    github_repository_size: float
    github_repository_language: Optional[str] = None
    github_repository_license: Optional[str] = None
    github_repository_url: str
    github_repository_website_url: Optional[str] = None
    github_repository_default_branch: str
    github_repository_is_private: bool
    github_repository_is_fork: bool
    github_repository_is_template: bool
    github_repository_is_archived: bool
    github_app_installation_id: int


class Import(BaseModel):
    pass


class InstallationsHttpResponse(BaseModel):
    installations: List[Installation]


class ImportsHttpResponse(BaseModel):
    imports: List[Import]


