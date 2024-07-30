from neptun import ERRORS, DIR_ERROR, FILE_ERROR, JSON_ERROR, UPDATE_CONFIG_ERROR, CONFIG_KEY_NOT_FOUND_ERROR, ID_ERROR, \
    NO_INTERNET_CONNECTION_ERROR


class BaseAppError(Exception):
    def __init__(self, code, message=None):
        self.code = code
        self.message = message or ERRORS.get(code, "Unknown error")
        super().__init__(self.message)


class DirError(BaseAppError):
    def __init__(self):
        super().__init__(DIR_ERROR)


class FileError(BaseAppError):
    def __init__(self):
        super().__init__(FILE_ERROR)


class JsonError(BaseAppError):
    def __init__(self):
        super().__init__(JSON_ERROR)


class UpdateConfigError(BaseAppError):
    def __init__(self):
        super().__init__(UPDATE_CONFIG_ERROR)


class ConfigKeyNotFoundError(BaseAppError):
    def __init__(self):
        super().__init__(CONFIG_KEY_NOT_FOUND_ERROR)


class IdError(BaseAppError):
    def __init__(self):
        super().__init__(ID_ERROR)


class NoInternetConnectionError(BaseAppError):
    def __init__(self):
        super().__init__(NO_INTERNET_CONNECTION_ERROR)


class NotAuthenticatedError(BaseAppError):
    def __init__(self):
        super().__init__(NO_INTERNET_CONNECTION_ERROR)
