from rich.console import Console
import typer
from neptun import ERRORS
from neptun.utils.managers import ConfigManager

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


@config_app.command(name="caching",
                    help="Enable/Disable request-caching.")
def configure_caching(val: str):
    if val not in ["True", "False", "true", "false"]:
        typer.secho(
            f'The value must be [True/False]!"',
            fg=typer.colors.RED,
        )
        raise typer.Abort()

    update_config_error = config_manager.update_config_dynamically(query=f"caching.caching_enabled={val}")

    if update_config_error:
        typer.secho(
            f'Failed to update configuration: "{ERRORS[update_config_error]}"',
            fg=typer.colors.RED,
        )
    else:
        typer.secho(f"Successfully set caching to {val}", fg=typer.colors.GREEN)


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


@config_app.command(name="init",
                    help="Init your neptun-configuration-file provided by the web-ui.")
def search_for_configuration_and_configure():
    use_provided_config = typer.confirm("Are you sure you want to use the custom configuration?")
    if not use_provided_config:
        raise typer.Abort()

    update_config_error = config_manager.search_for_configuration_and_configure()
