import webbrowser
from rich.console import Console
import typer
from neptun.utils.managers import ConfigManager
console = Console()

open_app = typer.Typer(name="Open", help="Open the Neptun web-interface.")
config_manager = ConfigManager()


@open_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        neptu_app_url = config_manager.read_config('utils', 'neptun_api_server_host').replace('api', 'home')
        try:
            chrome = webbrowser.get('chrome')
            chrome.open(neptu_app_url)
            console.print(
                f"Successfully launched the Neptun web-interface using {neptu_app_url}")
        except webbrowser.Error:
            typer.secho(
                f"Seems like chrome is not installed on your system.\nTo manually add open Neptun, please visit: {neptu_app_url}",
                fg=typer.colors.RED)
