from rich.console import Console
import typer
from typing_extensions import Annotated
from neptun import ERRORS
from neptun.utils.config_parser import ConfigManager

console = Console()
config_manager = ConfigManager()

config_app = typer.Typer(name="Configuration Manager", help="This tool allows you to manage and configure general "
                                                          "settings for your application with ease. You can add new "
                                                          "configurations, remove existing ones.")


def update_config_dynamically(query: Annotated[str, typer.Option("--query", "-q")]):
    update_config_error = config_manager.update_config_dynamically(query=query)
    if update_config_error:
        typer.secho(
            f'Failed to update configuration: "{ERRORS[update_config_error]}"',
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    else:
        typer.secho(f"Successfully updated the configuration with: {query}", fg=typer.colors.GREEN)


config_app.command(name="dynamic", help="Edit your app-settings dynamically")(update_config_dynamically)





