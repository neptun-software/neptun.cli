from typing import Tuple, List
from pydantic import BaseModel
from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer, Field, RootModel


class Post(BaseModel):
    user_id: int = Field(..., alias="userId")
    id: int
    title: str
    body: str

    def to_json(self):
        return self.dict(by_alias=True)


class PostHttpResponse(RootModel[List[Post]]):
    pass
