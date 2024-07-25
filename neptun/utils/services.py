from functools import wraps
from typing import List
import httpx
from pydantic import ValidationError
from neptun.model.http_requests import SignUpHttpRequest
from neptun.model.http_responses import PostHttpResponse, Post
from neptun.utils.exceptions import JsonError, FileError, UpdateConfigError, BaseAppError, NoInternetConnectionError


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class AuthenticationService:

    def __init__(self):
        self.client = httpx.Client()

    def login(self):

        pass

    def sign_up(self, sign_up_http_request: SignUpHttpRequest):
        return self.client.post('', json=sign_up_http_request.model_dump_json())


@singleton
class PostService:

    def __init__(self):
        self.client = httpx.Client()

    def get_posts(self) -> List[Post]:
        try:
            response = self.client.get('https://jsonplaceholder.typicode.com/posts')
            response.raise_for_status()
            return PostHttpResponse.parse_obj(response.json()).root
        except httpx.HTTPStatusError as e:
            raise JsonError() from e
        except httpx.RequestError as e:
            raise NoInternetConnectionError() from e
        except Exception as e:
            raise BaseAppError(-1, str(e)) from e


if __name__ == "__main__":
    post_service = PostService()

    print(post_service.get_posts())
