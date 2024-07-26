from functools import wraps
from typing import List, Union
import httpx
from httpx import AsyncClient
from pydantic import ValidationError
from neptun.utils.managers import ConfigManager
from neptun.model.http_requests import SignUpHttpRequest
from neptun.model.http_responses import SignUpResponse, ErrorResponse
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
        self.client = httpx.AsyncClient()
        self.config_manager = ConfigManager()

    def login(self):
        pass

    async def sign_up(self, sign_up_http_request: SignUpHttpRequest) -> Union[SignUpResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/auth/sign-up"

        async with self.client:
            response = await self.client.post(url, data=sign_up_http_request.dict())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("nuxai-session") else response.cookies.get("nuxai-session")
                sign_up_response = SignUpResponse.parse_obj(response_data)
                sign_up_response.session_cookie = session_cookie
                return sign_up_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)


if __name__ == "__main__":
    url = "https://example.com/api"  # Replace with your actual URL

    signup_http_request = SignUpHttpRequest(email='fopifdfis@dadyil.com', password='dnffdsfdsaffJ_89f')

    auth_service = AuthenticationService()

    result = auth_service.sign_up(sign_up_http_request=signup_http_request)

    if isinstance(result, SignUpResponse):
        print(f"User ID: {result.user.id}")
        print(f"Primary Email: {result.user.email}")
        print(f"Logged In At: {result.logged_in_at}")
        if result.session_cookie:
            print(f"Session Cookie: {result.session_cookie}")
    elif isinstance(result, ErrorResponse):
        print(f"Error {result.statusCode}: {result.statusMessage}")
        if result.data:
            for issue in result.data.issues:
                print(f" - {issue.message} (path: {'/'.join(issue.path)})")
        else:
            print("No additional error data available.")


