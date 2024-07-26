from datetime import time
from typing import Tuple, List, Optional
from pydantic import BaseModel
from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer, Field, RootModel


class User(BaseModel):
    id: int
    email: str = Field(..., alias='primary_email')

    def to_json(self):
        return self.dict(by_alias=True)


class SignUpResponse(BaseModel):
    user: User = Field(..., alias='user')
    session_cookie: str = None
    logged_in_at: str = Field(..., alias='loggedInAt')

    def to_json(self):
        return self.dict(by_alias=True)


class LoginResponse(BaseModel):
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
