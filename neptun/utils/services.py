from functools import wraps
from typing import Union
import httpx
from pydantic import ValidationError
from neptun.utils.exceptions import AuthenticationError
from neptun.utils.managers import ConfigManager
from neptun.model.http_requests import SignUpHttpRequest, LoginHttpRequest, CreateChatHttpRequest, ChatRequest, \
    OTPCreateRequest, ResetPasswordRequest, CreateCollectionRequest, CreateTemplateRequest, Template, \
    UpdateCollectionRequest, UpdateChatRequest, CreateNeptunProjectRequest
from neptun.model.http_responses import SignUpHttpResponse, GeneralErrorResponse, ErrorResponse, LoginHttpResponse, \
    ChatsHttpResponse, CreateChatHttpResponse, ChatMessagesHttpResponse, GithubAppInstallation, \
    GithubAppInstallationHttpResponse, GetInstallationsError, \
    GithubRepositoryHttpResponse, GetImportsError, GithubRepository, OTPResponse, ResetPasswordResponse, \
    AuthenticationErrorResponse, HealthCheckResponse, GetChatFilesResponse, TemplateCollectionResponse, \
    TemplateCollection, GetSharedCollectionsResponse, UpdateChatResponse, NeptunProject, CreateNeptunProjectResponse
from neptun.utils.helpers import ChatResponseConverter
import logging

logging.basicConfig(
    filename='app.log',  # Name of the log file
    filemode='a',  # Mode to open the file ('w' for overwrite, 'a' for append)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    level=logging.DEBUG  # Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


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
        id = self.config_manager.read_config(section="auth.user", key="id")
        neptun_session_token = self.config_manager.read_config(section="auth", key="neptun_session_cookie")

        # Pass the exception into kwargs if authentication fails
        if neptun_session_token is None or id is None:
            kwargs["authentication_error"] = AuthenticationError(message="Not authenticated")

        return method(self, *args, **kwargs)

    return wrapper


@singleton
class ApplicationService:
    def __init__(self):
        self.client = httpx.Client()
        self.config_manager = ConfigManager()

    def check_health(self) -> Union[HealthCheckResponse, GeneralErrorResponse]:
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host').removesuffix("/api")}/health"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                return HealthCheckResponse(**response.json())
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage="Server returned an error",
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Request failed: {str(e)}",
            )
        except Exception as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Unexpected error occurred: {str(e)}",
            )


@singleton
class AuthenticationService:
    def __init__(self):
        self.client = httpx.Client()
        self.config_manager = ConfigManager()

    def _get_session_cookie(self):
        """

        @rtype: str
        """
        cookie = self.config_manager.read_config("auth", "neptun_session_cookie")
        if not cookie:
            raise AuthenticationError(
                success=False,
                message="User is not authenticated. Please log in.",
                error_code=401
            )
        return cookie

    def check_authenticated(self, cookie):
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/auth/check"

        self.client.cookies.set('neptun-session', cookie)

        request = self.client.head(url)

        if request.status_code == 204:
            return True
        elif request.status_code == 401:
            return False

    def login(self, login_up_http_request: LoginHttpRequest) -> Union[LoginHttpResponse, ErrorResponse]:
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/auth/login"

        with self.client:
            response = self.client.post(url, data=login_up_http_request.model_dump())

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
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/auth/sign-up"

        with self.client:
            response = self.client.post(url, data=sign_up_http_request.model_dump())

            response_data = response.json()

            try:
                session_cookie = None if not response.cookies.get("neptun-session") else response.cookies.get(
                    "neptun-session")
                sign_up_response = SignUpHttpResponse.parse_obj(response_data)
                sign_up_response.session_cookie = session_cookie
                return sign_up_response
            except ValidationError:
                return ErrorResponse.parse_obj(response_data)

    def send_otp(self, email: str) \
            -> Union[OTPResponse, ErrorResponse, AuthenticationError]:
        try:
            cookie = self._get_session_cookie()
        except AuthenticationError as e:
            return AuthenticationError(success=False, message=str(e), error_code=e.error_code)

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host').removesuffix("/api")}/auth/otp"
        otp_request = OTPCreateRequest(email=email)

        self.client.cookies.set("neptun-session", cookie)
        response = self.client.post(url, json=otp_request.model_dump())
        response_data = response.json()

        try:
            return OTPResponse.model_validate(response_data)
        except ValidationError:
            return ErrorResponse.model_validate(response_data)

    def reset_password(self, otp: str, new_password: str) \
            -> Union[ResetPasswordResponse, ErrorResponse, AuthenticationError]:
        try:
            cookie = self._get_session_cookie()
        except AuthenticationError as e:
            return AuthenticationError(success=False, message=str(e), error_code=e.error_code)

        email = self.config_manager.read_config("auth.user", "email")
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host').removesuffix("/api")}/{email}/reset-password"
        reset_password_request = ResetPasswordRequest(otp=otp, new_password=new_password)

        self.client.cookies.set("neptun-session", cookie)
        response = self.client.post(url, json=reset_password_request.model_dump())
        response_data = response.json()

        try:
            self.close()
            return ResetPasswordResponse.model_validate(response_data)
        except ValidationError:
            return ErrorResponse.model_validate(response_data)

    def close(self):
        self.client.close()


@singleton
class ChatService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(cookies={"neptun-session": self.config_manager
                                   .read_config(section="auth",
                                                key="neptun_session_cookie")})
        self.async_client = httpx.AsyncClient(
            cookies={"neptun-session": self.config_manager.read_config(section="auth", key="neptun_session_cookie")}
        )
        self.chat_response_converter = ChatResponseConverter()
        self.auth_service = AuthenticationService()

    def _ensure_authenticated(self) -> Union[bool, GeneralErrorResponse]:
        try:
            cookie = self.auth_service._get_session_cookie()

            is_authenticated = self.auth_service.check_authenticated(cookie)
            if not is_authenticated:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Session cookie is invalid. Please log in again.",
                )

            return True
        except AuthenticationError as e:
            return GeneralErrorResponse(
                statusCode=401,
                statusMessage=str(e),
            )

    def get_available_ai_chats(self) -> Union[ChatsHttpResponse, GeneralErrorResponse]:

        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{id}/chats?order_by=updated_at:desc"

        response = self.client.get(url)

        response_data = response.json()

        try:
            chat_response = ChatsHttpResponse.model_validate(response_data)
            return chat_response
        except ValidationError:
            return GeneralErrorResponse.model_validate(response_data)

    def delete_selected_chat(self, chat_id) -> Union[bool, GeneralErrorResponse]:
        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        id = self.config_manager.read_config("auth.user", "id")
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{id}/chats/{chat_id}"

        response = self.client.delete(url)

        if response.status_code != 200:
            return GeneralErrorResponse(statusCode=response.status_code,
                                        statusMessage="Error occurred while deleting the selected chat.")
        else:
            return True

    def update_chat(self, chat_id: int, name: str, model: str) -> Union[UpdateChatResponse, GeneralErrorResponse]:
        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        user_id = int(self.config_manager.read_config("auth", "user_id"))
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/chats/{chat_id}"

        payload = UpdateChatRequest(name=name, model=model).dict()

        response = self.client.patch(url, json=payload)
        if response.status_code != 200:
            return GeneralErrorResponse(statusCode=response.status_code, statusMessage=response.text)

        return UpdateChatResponse(**response.json())

    def create_chat(self, create_chat_http_request: CreateChatHttpRequest) \
            -> Union[CreateChatHttpResponse, ErrorResponse, GeneralErrorResponse]:

        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        id = self.config_manager.read_config("auth.user", "id")

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{id}/chats"

        try:
            response = self.client.post(url, data=create_chat_http_request.model_dump())

            response_data = response.json()

            print(response_data)

            if 'chat' not in response_data or response_data['chat'] is None:
                return ErrorResponse(
                    statusCode=400,
                    statusMessage="Failed to create chat. The 'chat' field is missing or invalid."
                )

            try:
                chat_response = CreateChatHttpResponse.model_validate(response_data)
                return chat_response
            except ValidationError:
                return ErrorResponse.model_validate(response_data)

        except httpx.HTTPStatusError as http_error:
            return GeneralErrorResponse(
                statusCode=http_error.response.status_code,
                statusMessage=f"HTTP error occurred: {http_error}",
            )

        except Exception as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"An unexpected error occurred: {str(e)}",
            )

    async def get_chat_messages_by_chat_id(self) \
            -> Union[ChatMessagesHttpResponse, ErrorResponse]:
        user_id = self.config_manager.read_config("auth.user", "id")
        chat_id = self.config_manager.read_config("active_chat", "chat_id")

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/chats/{chat_id}/messages"

        response = await self.async_client.get(url)
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

    async def post_chat_message(self, messages: ChatRequest) -> Union[str, None]:
        try:
            chat_id = self.config_manager.read_config("active_chat", "chat_id")
            model = self.config_manager.read_config("active_chat", "model")
            model_publisher, model_name = self.extract_parts(model)

            logging.debug(f"Sent object: {messages.json()}")

            url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/ai/huggingface/{model_publisher}/{model_name}/chat?chat_id={chat_id}"
            logging.debug(f"Constructed URL: {url}")

            response = await self.async_client.post(url, json=messages.model_dump())

            logging.debug(f"Response received: {response.text}")

            response_data = self.chat_response_converter.parse_response(response=response.text)

            return response.text
        except ValidationError as ve:
            logging.error(f"Validation error: {ve}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        return None

    def get_chat_files(self) -> Union[GetChatFilesResponse, GeneralErrorResponse]:
        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        user_id = self.config_manager.read_config("auth.user", "id")
        chat_id = self.config_manager.read_config("active_chat", "chat_id")
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/chats/{chat_id}/files"

        try:
            response = self.client.get(url)

            if response.status_code == 200:
                return GetChatFilesResponse(**response.json())
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage=response.reason_phrase,
                )
        except ValidationError as ve:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage="Validation Error",
            )
        except Exception as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage="An unexpected error occurred",
            )


def parse_response(response: str) -> str:
    lines = response.splitlines()

    parsed_lines = []

    for line in lines:
        parsed_line = line.split(':')[1].strip().strip('"')
        parsed_lines.append(parsed_line)

    return ''.join(parsed_lines)


@singleton
class GithubService:

    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(cookies={"neptun-session": self.config_manager
                                   .read_config(section="auth",
                                                key="neptun_session_cookie")})
        self.auth_service = AuthenticationService()

    def _ensure_authenticated(self) -> Union[bool, GeneralErrorResponse]:
        try:
            cookie = self.auth_service._get_session_cookie()

            is_authenticated = self.auth_service.check_authenticated(cookie)
            if not is_authenticated:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Session cookie is invalid. Please log in again.",
                )

            return True
        except AuthenticationError as e:
            return GeneralErrorResponse(
                statusCode=401,
                statusMessage=str(e),
            )

    def get_installations_by_user_id(self) -> Union[
        GithubAppInstallationHttpResponse, GetInstallationsError, GeneralErrorResponse]:
        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        user_id = self.config_manager.read_config("auth.user", "id")

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/installations"

        response = self.client.get(url)
        response_data = response.json()

        try:
            installations_response = [GithubAppInstallation(**installation) for installation in response_data]
            return GithubAppInstallationHttpResponse(installations=installations_response)
        except ValidationError:
            return GetInstallationsError.model_validate(response_data)

    def get_repositories_for_installation(self, installation_id: int) -> Union[
        GithubRepositoryHttpResponse, GetImportsError, GeneralErrorResponse]:
        auth_check = self._ensure_authenticated()
        if isinstance(auth_check, GeneralErrorResponse):
            return auth_check

        user_id = self.config_manager.read_config("auth.user", "id")

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/installations/{installation_id}/imports"

        response = self.client.get(url)
        response_data = response.json()

        try:
            if isinstance(response_data, list):
                repositories_response = [GithubRepository(**repo) for repo in response_data]
                return GithubRepositoryHttpResponse(repositories=repositories_response)

            return GetImportsError.model_validate(response_data)
        except ValidationError as e:
            logging.error(f"Validation error while parsing response: {e}")
            raise


@singleton
class TemplateService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(cookies={"neptun-session": self.config_manager
                                   .read_config(section="auth",
                                                key="neptun_session_cookie")})
        self.auth_service = AuthenticationService()

    def close(self):
        self.client.close()

    def _ensure_authenticated(self) -> Union[bool, GeneralErrorResponse]:
        try:
            cookie = self.auth_service._get_session_cookie()

            is_authenticated = self.auth_service.check_authenticated(cookie)
            if not is_authenticated:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Session cookie is invalid. Please log in again.",
                )

            return True
        except AuthenticationError as e:
            return GeneralErrorResponse(
                statusCode=401,
                statusMessage=str(e),
            )

    def create_template(self, collection_id: int, create_template_request: CreateTemplateRequest) -> None | GeneralErrorResponse | ErrorResponse | Template:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/collections/{collection_id}/templates"

        try:
            response = self.client.post(url, json=create_template_request.dict())
            if response.status_code == 400:
                return ErrorResponse(
                    statusCode=400,
                    statusMessage="Invalid body format. Expected { template, file }"
                )
            elif response.status_code == 401:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Unauthorized. Invalid or missing session cookie."
                )
            elif response.status_code == 403:
                return GeneralErrorResponse(
                    statusCode=403,
                    statusMessage="Forbidden. User ID mismatch."
                )
            elif response.status_code == 404:
                return GeneralErrorResponse(
                    statusCode=404,
                    statusMessage="Collection not found."
                )
            elif response.status_code == 500:
                return GeneralErrorResponse(
                    statusCode=500,
                    statusMessage="Server error."
                )

            response_data = response.json()


            if response.status_code == 201:
                try:
                    template_response = Template.model_validate(response_data)
                    return template_response
                except ValidationError:
                    return ErrorResponse.model_validate(response_data)

        except httpx.HTTPStatusError as http_error:
            return GeneralErrorResponse(
                statusCode=http_error.response.status_code,
                statusMessage=f"HTTP error occurred: {http_error}",
            )

        except Exception as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"An unexpected error occurred: {str(e)}",
            )

    def delete_template(self, collection_id: int, template_id: int) -> Union[bool, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))
        url = (
            f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}"
            f"/users/{user_id}/collections/{collection_id}/templates/{template_id}"
        )
        try:
            response = self.client.delete(url, headers={"Accept": "application/json"})
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                return GeneralErrorResponse(statusCode=404, statusMessage="Template not found")
            elif response.status_code == 401:
                return GeneralErrorResponse(statusCode=401,
                                            statusMessage="Unauthorized. Invalid or missing session cookie.")
            elif response.status_code == 403:
                return GeneralErrorResponse(statusCode=403, statusMessage="Forbidden. User ID mismatch.")
            elif response.status_code == 500:
                return GeneralErrorResponse(statusCode=500, statusMessage="Server error.")
            else:
                return GeneralErrorResponse(statusCode=response.status_code, statusMessage=response.text)
        except httpx.RequestError as e:
            return GeneralErrorResponse(statusCode=500, statusMessage=f"Server error: {str(e)}")


@singleton
class CollectionService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(cookies={"neptun-session": self.config_manager
                                   .read_config(section="auth",
                                                key="neptun_session_cookie")})
        self.auth_service = AuthenticationService()

    def close(self):
        self.client.close()

    def _ensure_authenticated(self) -> Union[bool, GeneralErrorResponse]:
        try:
            cookie = self.auth_service._get_session_cookie()

            is_authenticated = self.auth_service.check_authenticated(cookie)
            if not is_authenticated:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Session cookie is invalid. Please log in again.",
                )

            return True
        except AuthenticationError as e:
            return GeneralErrorResponse(
                statusCode=401,
                statusMessage=str(e),
            )

    def create_template_collection(self, create_collection_request: CreateCollectionRequest) -> Union[
        TemplateCollectionResponse, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))

        create_collection_request.neptun_user_id = user_id

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/collections"

        response = self.client.post(
            url,
            json=create_collection_request.model_dump(),
        )
        if response.status_code == 200:
            response_data = response.json()
            collection = TemplateCollection(**response_data['collection'])
            return TemplateCollectionResponse(collections=[collection])
        else:
            return GeneralErrorResponse(
                statusCode=response.status_code,
                statusMessage=response.text,
            )

    def get_user_template_collections(self) -> Union[TemplateCollectionResponse, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/collections"

        try:
            response = self.client.get(
                url
            )
            if response.status_code == 200:
                response_data = response.json()
                collections = [TemplateCollection(**collection) for collection in response_data["collections"]]
                return TemplateCollectionResponse(collections=collections)
            elif response.status_code == 403:
                return GeneralErrorResponse(
                    statusCode=403,
                    statusMessage="Forbidden. User ID mismatch or insufficient permissions.",
                )
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage=response.text,
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Server error: {str(e)}",
            )

    def delete_template_collection(self, collection_id: int) -> Union[bool, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/collections/{collection_id}"

        try:
            response = self.client.delete(url)
            response.raise_for_status()

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                return GeneralErrorResponse(statusCode=404, statusMessage="Collection not found")
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage=f"Failed to delete collection: {response.text}",
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Server error: {str(e)}",
            )
        finally:
            self.auth_service.close()

    def update_template_collection(self, id: int, update_request: UpdateCollectionRequest) -> Union[
        TemplateCollectionResponse, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))
        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/users/{user_id}/collections/{id}"

        try:
            response = self.client.patch(
                url,
                json=update_request.dict(),
            )

            if response.status_code == 200:
                response_data = response.json()
                updated_collection = TemplateCollection(**response_data['collection'])
                return TemplateCollectionResponse(collections=[updated_collection])
            elif response.status_code == 404:
                return GeneralErrorResponse(
                    statusCode=404,
                    statusMessage="Collection not found",
                )
            elif response.status_code == 403:
                return GeneralErrorResponse(
                    statusCode=403,
                    statusMessage="Forbidden. User ID mismatch or insufficient permissions.",
                )
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage=response.text,
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Server error: {str(e)}",
            )

    def get_shared_collections(self) -> Union[GetSharedCollectionsResponse, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        url = f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/shared/collections"
        try:
            response = self.client.get(
                url,
                headers={"Accept": "application/json"}
            )
            if response.status_code == 200:
                response_data = response.json()
                return GetSharedCollectionsResponse(**response_data)
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code,
                    statusMessage=f"Failed to retrieve shared collections: {response.text}"
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500,
                statusMessage=f"Server error: {str(e)}"
            )


@singleton
class ProjectService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.client = httpx.Client(
            cookies={
                "neptun-session": self.config_manager.read_config(
                    section="auth", key="neptun_session_cookie"
                )
            }
        )
        self.auth_service = AuthenticationService()

    def close(self):
        self.client.close()

    def _ensure_authenticated(self) -> Union[bool, GeneralErrorResponse]:
        try:
            cookie = self.auth_service._get_session_cookie()
            is_authenticated = self.auth_service.check_authenticated(cookie)
            if not is_authenticated:
                return GeneralErrorResponse(
                    statusCode=401,
                    statusMessage="Session cookie is invalid. Please log in again.",
                )
            return True
        except Exception as e:
            return GeneralErrorResponse(statusCode=401, statusMessage=str(e))

    def create_project(
        self, create_project_request: CreateNeptunProjectRequest
    ) -> Union[CreateNeptunProjectResponse, GeneralErrorResponse]:
        authenticated = self._ensure_authenticated()
        if isinstance(authenticated, GeneralErrorResponse):
            return authenticated

        user_id = int(self.config_manager.read_config("auth.user", "id"))

        url = (
            f"{self.config_manager.read_config('utils', 'neptun_api_server_host')}/"
            f"users/{user_id}/projects"
        )

        try:
            response = self.client.post(
                url,
                json=create_project_request.model_dump(),
                headers={"Accept": "application/json"},
            )
            print(response.json())
            response.raise_for_status()

            if response.status_code == 201:
                response_data = response.json()
                project = NeptunProject(**response_data)
                return CreateNeptunProjectResponse(project=project)
            else:
                return GeneralErrorResponse(
                    statusCode=response.status_code, statusMessage=response.text
                )
        except httpx.RequestError as e:
            return GeneralErrorResponse(
                statusCode=500, statusMessage=f"Server error: {str(e)}"
            )


if __name__ == "__main__":
    github_service = GithubService()
    result = github_service.get_installations_by_user_id()

    if isinstance(result, GithubAppInstallationHttpResponse):
        for installation in result.installations:
            print(f"Installation ID: {installation.id}, Account Name: {installation.github_account_name}")
    elif isinstance(result, GetInstallationsError):
        print(f"Error {result.statusCode}: {result.statusMessage}")
        print(f"Details: {result.data.get('message')}")
