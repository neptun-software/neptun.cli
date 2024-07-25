import configparser
from functools import wraps
from pathlib import Path
from typing import List
import typer
from neptun.model.responses import ConfigResponse
import httpx
from neptun import SUCCESS, CONFIG_KEY_NOT_FOUND_ERROR, __app_name__, DIR_ERROR, FILE_ERROR
import json
from neptun.model.http_responses import PostHttpResponse, Post
from neptun.utils.services import AuthenticationService, PostService


CONFIG_DIR_PATH = Path(typer.get_app_dir(__app_name__))
CONFIG_FILE_PATH = CONFIG_DIR_PATH / "config/config.ini"
DEFAULT_CONFIG_FILE_PATH = CONFIG_DIR_PATH / "config/default.json"

DEFAULT_CONFIG = json.load(open(Path(DEFAULT_CONFIG_FILE_PATH))) if Path(DEFAULT_CONFIG_FILE_PATH).exists() else None


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def ensure_latest_config(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self.config.read(self.config_file_path)
        return method(self, *args, **kwargs)
    return wrapper


@singleton
class ConfigManager:
    def __init__(self, config_file_path=CONFIG_FILE_PATH):
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self._ensure_config_file_exists()

    def set_config_file_path(self, path: str):
        self.config_file_path = path
        self._ensure_config_file_exists()
        self.config.read(self.config_file_path)

    def _write_default_config(self):
        """Write the default configuration to the file."""
        with open(self.config_file_path, 'w') as configfile:
            self._write_section(configfile, "", DEFAULT_CONFIG)

    def _write_section(self, file, parent_section, section_dict, level=0):
        """Write a section and its nested sections to the file."""
        for key, value in section_dict.items():
            section_name = f"{parent_section}.{key}" if parent_section else key
            if isinstance(value, dict):
                file.write(f"\n[{section_name}]\n")
                self._write_section(file, section_name, value, level + 1)
            else:
                file.write(f"{key} = {value}\n")

    def _ensure_config_file_exists(self):
        """Ensure the configuration directory and file exist."""
        if not CONFIG_DIR_PATH.exists():
            CONFIG_DIR_PATH.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE_PATH.exists():
            CONFIG_FILE_PATH.touch()
            self._write_default_config()

    @ensure_latest_config
    def read_config(self, section: str, key: str) -> str:
        return self.config[section][key]

    @ensure_latest_config
    def write_config(self, section: str, key: str, value: str):
        if section not in self.config:
            self.config.add_section(section)

        self.config[section][key] = value

        with open(self.config_file_path, 'w') as configfile:
            self.config.write(configfile)

    @ensure_latest_config
    def update_config(self, section: str, key: str, value: str) -> ConfigResponse:
        if section in self.config.sections() and key in self.config[section].keys():
            self.config[section][key] = value

            with open(self.config_file_path, 'w') as configfile:
                self.config.write(configfile)

            return SUCCESS
        else:
            return CONFIG_KEY_NOT_FOUND_ERROR

    @ensure_latest_config
    def delete_config(self, section: str, key: str):
        if section in self.config and key in self.config[section]:
            self.config.remove_option(section, key)

            with open(self.config_file_path, 'w') as configfile:
                self.config.write(configfile)

            print(f"Configuration '{key}' removed from section '{section}'")
        else:
            print(f"Configuration '{key}' in section '{section}' does not exist")

    @ensure_latest_config
    def list_sections(self):
        sections = self.config.sections()
        print("Sections:")
        for section in sections:
            print(f"  {section}")

        return sections

    @ensure_latest_config
    def list_keys(self, section: str):
        if section in self.config:
            keys = self.config[section].keys()
            print(f"Keys in section '{section}':")
            for key in keys:
                print(f"  {key}")

            return keys
        else:
            print(f"Section '{section}' does not exist")
            return []

    @ensure_latest_config
    def update_config_dynamically(self, query: str) -> ConfigResponse:
        section_value, rest = query.split('=', 1)

        value = rest
        key = section_value.split('.')[-1]
        section = '.'.join(section_value.split('.')[:-1])

        return self.update_config(section, key, value)

    def update_with_fallback(self) -> ConfigResponse:
        try:
            self._write_default_config()
            return SUCCESS
        except FileNotFoundError:
            return DIR_ERROR

    @ensure_latest_config
    def get_config_as_dict(self) -> dict:
        return {section: dict(self.config[section]) for section in self.config.sections()}

    @classmethod
    def init_app(cls, db_path: str) -> int:
        config_code = cls._init_config_file()
        if config_code != SUCCESS:
            return config_code
        return SUCCESS

    @staticmethod
    def _init_config_file() -> int:
        """Ensure the configuration directory and file are created."""
        try:
            CONFIG_DIR_PATH.mkdir(parents=True, exist_ok=True)
        except OSError:
            return DIR_ERROR
        try:
            CONFIG_FILE_PATH.touch(exist_ok=True)
        except OSError:
            return FILE_ERROR
        return SUCCESS


@singleton
class AuthenticationManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.auth_service = AuthenticationService()

    def login(self, username, password) -> ConfigResponse:

        pass

    def register(self, username, password) -> ConfigResponse:
        pass

    def request_auth_token(self, username, password) -> ConfigResponse:
        pass


@singleton
class PostManager:
    def __init__(self):
        self.post_service = PostService()

    def get_posts(self) -> List[Post]:
        return self.post_service.get_posts()


# Example usage
if __name__ == "__main__":

    config_manager_ini = ConfigManager()

    config_manager_ini.update_config_dynamically("auth.user.id=penis")

    config_manager_ini.list_sections()
    config_manager_ini.update_config("auth.user", "id", "hallo")

