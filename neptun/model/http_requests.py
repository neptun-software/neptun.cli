import json
from typing import List
from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer, Field, RootModel
import httpx


class SignUpHttpRequest(BaseModel):
    email: str = Field(serialization_alias="email")
    password: str


class LoginHttpRequest(BaseModel):
    email: str = Field(serialization_alias="email")
    password: str


class Post(BaseModel):
    user_id: int = Field(..., alias="userId")
    id: int
    title: str
    body: str

    def to_json(self):
        return self.dict(by_alias=True)


class PostHttpResponse(RootModel[List[Post]]):
    pass


if __name__ == '__main__':

    # get
    response = httpx.get('https://jsonplaceholder.typicode.com/posts')

    posts = PostHttpResponse.parse_obj(response.json())

    '''
    for post in posts.root:
        print(post.model_dump_json())
    '''

    post = Post(userId=2, id=1, title='testd', body='tedst')

    # post
    post_response = httpx.post('https://jsonplaceholder.typicode.com/posts', json=post.to_json())

    new_post = Post.parse_obj(post_response.json())

    print(new_post.body)






