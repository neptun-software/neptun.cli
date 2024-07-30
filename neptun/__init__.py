__app_name__ = "neptun"
__version__ = "0.1.0"

(
    SUCCESS,
    DIR_ERROR,
    FILE_ERROR,
    JSON_ERROR,
    UPDATE_CONFIG_ERROR,
    CONFIG_KEY_NOT_FOUND_ERROR,
    NO_INTERNET_CONNECTION_ERROR,
    NOT_AUTHENTICATED_ERROR,
    ID_ERROR,
) = range(9)

ERRORS = {
    DIR_ERROR: "config directory error",
    FILE_ERROR: "config file error",
    UPDATE_CONFIG_ERROR: "update config error",
    CONFIG_KEY_NOT_FOUND_ERROR: "config key not found error",
    NO_INTERNET_CONNECTION_ERROR: "internet connection error",
    NOT_AUTHENTICATED_ERROR: "authentication error"

}
