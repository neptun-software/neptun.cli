from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
    data: Optional[ErrorResponseData] = None


class Chat(BaseModel):
    id: int
    name: str
    model: str
    created_at: str
    neptun_user_id: Optional[int]


class UpdateChatResponse(BaseModel):
    chat: Chat


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


class GithubAppInstallation(BaseModel):
    id: int
    github_account_name: str
    github_account_type: str
    github_account_avatar_url: str
    created_at: datetime
    updated_at: datetime


class GithubAppInstallationHttpResponse(BaseModel):
    installations: list[GithubAppInstallation]


class GetInstallationsError(BaseModel):
    statusCode: int
    statusMessage: str
    data: dict[str, str]


class GithubRepository(BaseModel):
    id: int
    github_repository_id: int
    github_repository_name: str
    github_repository_description: Optional[str] = None
    github_repository_size: Optional[int] = None
    github_repository_language: Optional[str] = None
    github_repository_license: Optional[str] = None
    github_repository_url: str
    github_repository_website_url: Optional[str] = None
    github_repository_default_branch: Optional[str] = None
    github_repository_is_private: bool
    github_repository_is_fork: Optional[bool] = None
    github_repository_is_template: Optional[bool] = None
    github_repository_is_archived: bool
    created_at: str
    updated_at: str
    github_app_installation_id: int


class GithubRepositoryHttpResponse(BaseModel):
    repositories: list[GithubRepository]


class GetImportsError(BaseModel):
    statusCode: int
    statusMessage: str
    data: dict[str, str]


class OTPResponse(BaseModel):
    success: bool
    message: str


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str


class AuthenticationErrorResponse(BaseModel):
    success: bool
    message: str
    error_code: int


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float


class ChatFile(BaseModel):
    id: int
    chat_conversation_id: int
    chat_conversation_message_id: int
    neptun_user_id: int
    title: str
    text: str
    language: str = "text"
    extension: str = "txt"
    created_at: datetime
    updated_at: datetime


class GetChatFilesResponse(BaseModel):
    chatFiles: List[ChatFile]


class Template(BaseModel):
    id: int
    description: Optional[str]
    file_name: str
    created_at: datetime
    updated_at: datetime
    neptun_user_id: int
    template_collection_id: Optional[int]
    user_file_id: Optional[int]


class TemplateCollection(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_shared: bool
    share_uuid: str
    created_at: str
    updated_at: str
    neptun_user_id: Optional[int] = -1
    templates: Optional[List] = None


class CreateTemplateResponse(BaseModel):
    template: Template


class TemplateCollectionResponse(BaseModel):
    collections: list[TemplateCollection]


class GetSharedCollectionsResponse(BaseModel):
    collections: List[TemplateCollection]
    total: int


class GetSharedCollectionsError(BaseModel):
    statusCode: int
    statusMessage: str
    message: str


class NeptunProject(BaseModel):
    id: int
    name: str
    description: Optional[str]
    project_type: str
    programming_language: str
    created_at: datetime
    updated_at: datetime
    neptun_user_id: int


class CreateNeptunProjectResponse(BaseModel):
    project: NeptunProject
