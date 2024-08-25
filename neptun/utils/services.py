import asyncio
import json
from functools import wraps
from typing import Union
import re
import httpx
from pydantic import ValidationError
from neptun.utils.managers import ConfigManager
from neptun.model.http_requests import SignUpHttpRequest, LoginHttpRequest, CreateChatHttpRequest, Message, ChatRequest
from neptun.model.http_responses import SignUpHttpResponse, GeneralErrorResponse, ErrorResponse, LoginHttpResponse, \
    ChatsHttpResponse, CreateChatHttpResponse, ChatMessagesHttpResponse
from neptun.utils.exceptions import NotAuthenticatedError
from neptun.utils.helpers import ChatResponseConverter, ResponseContent


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
        self.client = httpx.Client()
        self.config_manager = ConfigManager()

    def login(self, login_up_http_request: LoginHttpRequest) -> Union[LoginHttpResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/auth/login"

        with self.client:
            response = self.client.post(url, data=login_up_http_request.dict())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("neptun-session") else response.cookies.get(
                    "neptun-session")
                login_response = LoginHttpResponse.parse_obj(response_data)
                login_response.session_cookie = session_cookie
                return login_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)

    def sign_up(self, sign_up_http_request: SignUpHttpRequest) -> Union[SignUpHttpResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/auth/sign-up"

        with self.client:
            response = self.client.post(url, data=sign_up_http_request.dict())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("neptun-session") else response.cookies.get(
                    "neptun-session")
                sign_up_response = SignUpHttpResponse.parse_obj(response_data)
                sign_up_response.session_cookie = session_cookie
                return sign_up_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)


@singleton
class ChatService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(cookies={"neptun-session": self.config_manager
                                   .read_config(section="auth",
                                                key="neptun_session_cookie")})
        self.async_client = httpx.AsyncClient(
            cookies={"neptun-session": self.config_manager
                                    .read_config(section="auth",
                                            key="neptun_session_cookie")}
        )

    def get_available_ai_chats(self):
        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config("utils",
                                                 "neptun_api_server_host")}/users/{id}/chats?order_by=updated_at:desc"

        response = self.client.get(url)

        response_data = response.json()

        try:
            chat_response = ChatsHttpResponse.model_validate(response_data)
            return chat_response
        except ValidationError:
            return GeneralErrorResponse.model_validate(response_data)

    def delete_selected_chat(self, chat_id):

        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config("utils",
                                                 "neptun_api_server_host")}/users/{id}/chats/{chat_id}"

        try:
            response = self.client.delete(url)
            return True
        except Exception:
            return False

    def create_chat(self, create_chat_http_request: CreateChatHttpRequest) \
            -> Union[CreateChatHttpResponse, ErrorResponse]:
        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/users/{id}/chats"

        response = self.client.post(url, data=create_chat_http_request.dict())

        response_data = response.json()

        try:
            chat_response = CreateChatHttpResponse.model_validate(response_data)
            return chat_response
        except ValidationError:
            return ErrorResponse.model_validate(response_data)

    def get_chat_messages_by_chat_id(self) \
            -> Union[ChatMessagesHttpResponse, ErrorResponse]:
        user_id = self.config_manager.read_config("auth.user", "id")
        chat_id = self.config_manager.read_config("active_chat", "chat_id")

        url = f"{self.config_manager.read_config("utils", "neptun_api_server_host")}/users/{user_id}/chats/{chat_id}/messages"

        response = self.client.get(url)
        response_data = response.json()

        try:
            chat_messages_http_response = ChatMessagesHttpResponse.model_validate(response_data)
            return chat_messages_http_response
        except ValidationError:
            return ErrorResponse.model_validate(response_data)

    def extract_parts(self, s: str):
        before_slash = s.split('/')[0]
        after_slash = s.split('/')[1] if '/' in s else ''
        return before_slash, after_slash

    def post_chat_message(self, messages: ChatRequest) -> str:
        chat_id = self.config_manager.read_config("active_chat", "chat_id")
        model = self.config_manager.read_config("active_chat", "model")
        model_publisher, model_name = self.extract_parts(model)

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/ai/huggingface/{model_publisher}/{model_name}/chat?chat_id={chat_id}"

        response = self.client.post(url, json=messages.dict())

        response_data = response.text

        try:
            return response_data
        except ValidationError:
            print("error")


def clean_text(text_str: str) -> str:
    # Clean up text content (if needed)
    cleaned_text = re.sub(r'\\n', '\n', text_str)  # Replace literal \n with actual newline
    cleaned_text = re.sub(r'\\\\"', '"""', cleaned_text)  # Replace \\" with """
    cleaned_text = re.sub(r'\\"', '"', cleaned_text)  # Replace \" with "
    cleaned_text = re.sub(r'\\\\', '\\', cleaned_text)  # Replace \\\\ with \
    cleaned_text = re.sub(r'\\', '', cleaned_text)  # Remove any remaining single backslashes
    return cleaned_text


if __name__ == "__main__":
    url = "https://example.com/api"  # Replace with your actual URL

    chat_service = ChatService()

    # Create a message
    message = Message(role="user", content="Generate me fizzbuzz in java!")

    message_list = [message]

    messages = ChatRequest(messages=message_list)

    try:
        result = chat_service.post_chat_message(messages)

        chat_converter = ChatResponseConverter(message=result)

        for section in chat_converter.extract_sections():
            if isinstance(section, ResponseContent):
                if section.type == "markdown":
                    # Process markdown section
                    print(f'```\n{section.content}\n```')
                elif section.type == "text":
                    # Process text section
                    print(f'```\n{section.content}\n```')

            else:
                print("Unexpected section type:", type(section))

    except NotAuthenticatedError:
        print("Not authenticated!")
