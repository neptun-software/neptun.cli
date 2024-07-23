import configparser
from functools import wraps
from pathlib import Path
import typer
from neptun.model.responses import ConfigResponse
from neptun import SUCCESS, CONFIG_KEY_NOT_FOUND_ERROR, __app_name__, DIR_ERROR, FILE_ERROR

# Define global paths
CONFIG_DIR_PATH = Path(typer.get_app_dir(__app_name__))
CONFIG_FILE_PATH = CONFIG_DIR_PATH / "config/config.ini"


DEFAULT_CONFIG = {
    "caching": {
        "caching_enabled": "True",
        "cache_name": "cache/neptun_cache",
        "cache_expiration": "600"
    },
    "auth": {
        "neptun_auth_token": ""
    },
}


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
        for section, options in DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
        with open(self.config_file_path, 'w') as configfile:
            self.config.write(configfile)

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
        section, rest = query.split('.', 1)
        key, value = rest.split('=', 1)
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

    def login(self, username, password) -> ConfigResponse:
        pass

    def register(self, username, password) -> ConfigResponse:
        pass

    def request_auth_token(self, username, password) -> ConfigResponse:
        pass


# Example usage
if __name__ == "__main__":
    # Instantiate ConfigManager for INI file
    config_manager_ini = ConfigManager()

    config_manager_ini.list_sections()
    config_manager_ini.update_config("auth", "neptun_auth_token", "pimmel")

