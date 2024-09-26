import typer
import webbrowser
from rich.console import Console
from neptun.utils.managers import ConfigManager
from neptun.utils.services import AuthenticationService

config_manager = ConfigManager()
console = Console()
authentication_service = AuthenticationService()


github_app = typer.Typer(name="Github Manager",
                         help="Manage your imported repositories & use the neptun gh-application.")


@github_app.command(name="install",
                    help="Install the official neptun-github-application onto a repository.")
def install_github_app():
    github_app_url = config_manager.read_config('utils', 'neptun_github_app_url')
    try:
        chrome = webbrowser.get('chrome')
        chrome.open(github_app_url)
        console.print(f"Successfully launched chrome. You are ready to install the neptun-github-application!\nYou can find the installed application here: https://neptun-webui.vercel.app/account")
    except webbrowser.Error:
        typer.secho("Seems like chrome is not installed on your system.\nTo manually add the github-application, please visit: https://github.com/apps/neptun-github-app/installations", fg=typer.colors.RED)


