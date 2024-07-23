from functools import wraps
from neptun.model.responses import ConfigResponse
from neptun.utils.config_parser import ConfigManager


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class AuthenticationManager:
    def __init__(self):
        self.config_manager = ConfigManager()

    def login(self, username, password) -> ConfigResponse:
        pass

    def register(self, username, password) -> ConfigResponse:
        pass

    def request_auth_token(self, username, password) -> ConfigResponse:
        pass

