from rich.console import Console
import typer
from neptun import ERRORS
from neptun.utils.managers import ConfigManager
from rich.table import Table


console = Console()
config_manager = ConfigManager()

config_app = typer.Typer(name="Configuration Manager", help="This tool allows you to manage and configure general "
                                                          "settings for your application with ease. You can add new "
                                                          "configurations, remove existing ones.")


@config_app.command(name="dynamic",
                    help="Edit your app-settings dynamically")
def update_config_dynamically(query: str):
    update_config_error = config_manager.update_config_dynamically(query=query)
    if update_config_error:
        typer.secho(
            f'Failed to update configuration: "{ERRORS[update_config_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    else:
        typer.secho(f"Successfully updated the configuration with: {query}", fg=typer.colors.GREEN)


@config_app.command(name="fallback",
                    help="Fallback to the default settings if you have messed up the configuration file.")
def update_with_fallback():
    fallback = typer.confirm("Are you sure you want to fallback to the default configuration?")
    if not fallback:
        raise typer.Abort()

    update_config_error = config_manager.update_with_fallback()
    if update_config_error:
        typer.secho(
            f'Failed to update configuration: "{ERRORS[update_config_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    else:
        typer.secho(f"Successfully updated the configuration with the fallback.", fg=typer.colors.GREEN)


@config_app.command(name="session-token",
                    help="Update your neptun-auth-token.")
def configure_auth_token(val: str):
    update_config_error = config_manager.update_config_dynamically(query=f"auth.neptun_session_cookie={val}")

    if update_config_error:
        typer.secho(
            f'Failed to update configuration: "{ERRORS[update_config_error]}"',
            fg=typer.colors.RED,
        )
    else:
        typer.secho(f"Successfully set auth-key to: {val}", fg=typer.colors.GREEN)


@config_app.command(name="init", help="Init your neptun-configuration-file provided by the web-ui.")
def search_for_configuration_and_configure():
    use_provided_config = typer.confirm("Are you sure you want to use the custom configuration?")

    if not use_provided_config:
        raise typer.Abort()

    try:
        update_config_error = config_manager.search_for_configuration_and_configure()

        if update_config_error:
            typer.secho("Configuration failed. Please check the details and try again.", fg=typer.colors.RED)
        else:
            typer.secho("Configuration was successful!", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED)


@config_app.command(name="status",
                  help="Get your current configuration-status and user-data if provided.")
def status():
    neptun_session_cookie = config_manager.read_config('auth', 'neptun_session_cookie')
    email = config_manager.read_config('auth.user', 'email')
    chat_name = config_manager.read_config('active_chat', 'chat_name')
    chat_model = config_manager.read_config('active_chat', 'model')
    neptun_api_host = config_manager.read_config('utils', 'neptun_api_server_host')

    is_authenticated = neptun_session_cookie not in [None, "None", ""]

    table = Table(title="Current Configuration Status")

    table.add_column("Email", justify="left", no_wrap=True)
    table.add_column("Cookie", justify="left", no_wrap=True)
    table.add_column("NeptunAPIHost", justify="left", no_wrap=True)
    table.add_column("ChatName", justify="left", no_wrap=True)
    table.add_column("ChatModel", justify="left", no_wrap=True)

    table.add_row(
        email if email else "No Email Found",
        f"{neptun_session_cookie[:5]}..." if is_authenticated else "No Cookie",
        neptun_api_host if neptun_api_host else "No API-Host Found",
        chat_name if chat_name else "No Chat Name Found",
        chat_model if chat_model else "No Chat Model Found",
    )

    console.print(table)

