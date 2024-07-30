import asyncio
from functools import wraps
from typing import Union
import httpx
from pydantic import ValidationError
from neptun.utils.managers import ConfigManager
from neptun.model.http_requests import SignUpHttpRequest, LoginHttpRequest
from neptun.model.http_responses import SignUpResponse, GeneralErrorResponse, ErrorResponse, LoginResponse, \
    ChatsResponse
from neptun.utils.exceptions import NotAuthenticatedError
import httpx_cache


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def ensure_authenticated(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        id = self.config_manager.read_config(section='auth.user', key='id')
        neptun_session_token = self.config_manager.read_config(section='auth', key='neptun_session_cookie')

        if neptun_session_token is None or id is None:
            raise NotAuthenticatedError()

        return method(self, *args, **kwargs)

    return wrapper


@singleton
class AuthenticationService:

    def __init__(self):
        self.client = httpx.AsyncClient()
        self.config_manager = ConfigManager()

    async def login(self, login_up_http_request: LoginHttpRequest) -> Union[LoginResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/auth/login"

        async with self.client:
            response = await self.client.post(url, data=login_up_http_request.dict())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("nuxai-session") else response.cookies.get(
                    "nuxai-session")
                login_response = LoginResponse.parse_obj(response_data)
                login_response.session_cookie = session_cookie
                return login_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)

    async def sign_up(self, sign_up_http_request: SignUpHttpRequest) -> Union[SignUpResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/auth/sign-up"

        async with self.client:
            response = await self.client.post(url, data=sign_up_http_request.dict())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("nuxai-session") else response.cookies.get(
                    "nuxai-session")
                sign_up_response = SignUpResponse.parse_obj(response_data)
                sign_up_response.session_cookie = session_cookie
                return sign_up_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)


@singleton
class ChatService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx_cache.AsyncClient(cookies={"nuxai-session": self.config_manager
                                              .read_config(section="auth",
                                                           key="neptun_session_cookie")})

    async def get_available_ai_chats(self):
        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/users/{id}/chats"

        async with self.client:
            response = await self.client.get(url)

            response_data = response.json()

            try:
                chat_response = ChatsResponse.parse_obj(response_data)
                return chat_response
            except ValidationError:
                return GeneralErrorResponse.parse_obj(response_data)


if __name__ == "__main__":
    url = "https://example.com/api"  # Replace with your actual URL

    chat_service = ChatService()

    try:
        result = asyncio.run(chat_service.get_available_ai_chats())

        if isinstance(result, ChatsResponse):
            print(result)
        elif isinstance(result, GeneralErrorResponse):
            print(result.statusMessage)
    except NotAuthenticatedError:
        print("Not authenticated!")
