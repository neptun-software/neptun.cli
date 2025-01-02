import typer
import webbrowser
from rich.console import Console
from neptun.utils.managers import ConfigManager
from neptun.utils.services import AuthenticationService, GithubService
from neptun.model.http_responses import GetInstallationsError, GithubAppInstallationHttpResponse

config_manager = ConfigManager()
console = Console()
authentication_service = AuthenticationService()
github_service = GithubService()

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


@github_app.command(name="installations", help="List all GitHub app installations")
def list_github_installations():
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Collecting GitHub app installations...",
                          total=None)

        result = github_service.get_installations_by_user_id()

        if isinstance(result, GithubAppInstallationHttpResponse):
            progress.stop()
            table = Table()
            table.add_column("ID", justify="left", no_wrap=True)
            table.add_column("Account Name", justify="left", no_wrap=True)
            table.add_column("Account Type", justify="left", no_wrap=True)
            table.add_column("Created At", justify="left", no_wrap=True)
            table.add_column("Updated At", justify="left", no_wrap=True)

            # Add rows for each installation
            for installation in result.installations:
                table.add_row(
                    f"{installation.id}",
                    f"{installation.github_account_name}",
                    f"{installation.github_account_type}"
                )
            console.print(table)
        elif isinstance(result, GetInstallationsError):
            progress.stop()
            typer.secho(f"Error {result.statusCode}: {result.statusMessage}",
                        fg=typer.colors.RED)
            if result.data and "message" in result.data:
                typer.secho(f"Details: {result.data['message']}", fg=typer.colors.YELLOW)

            typer.secho("It seems no GitHub app installations were found. "
                        "Would you like to install the Neptun GitHub application?",
                        fg=typer.colors.YELLOW)

            install_now = questionary.confirm("Do you want to open the installation page?").ask()

            if install_now:
                github_app_url = config_manager.read_config('utils', 'neptun_github_app_url')
                try:
                    chrome = webbrowser.get('chrome')
                    chrome.open(github_app_url)
                    console.print("Successfully launched Chrome. You can install the Neptun GitHub application here:\n"
                                  "https://neptun-webui.vercel.app/account")
                except webbrowser.Error:
                    typer.secho("It seems Chrome is not installed on your system.\n"
                                "To manually install the GitHub application, please visit:\n"
                                "https://github.com/apps/neptun-github-app/installations",
                                fg=typer.colors.RED)
        else:
            progress.stop()
            typer.secho("Unexpected error occurred while fetching GitHub installations.",
                        fg=typer.colors.RED)