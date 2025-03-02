import webbrowser
from neptun.utils.managers import ConfigManager
from neptun.utils.services import AuthenticationService, GithubService
from neptun.model.http_responses import GetInstallationsError, GithubAppInstallationHttpResponse, GithubRepositoryHttpResponse, GeneralErrorResponse
import questionary
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

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


@github_app.command(name="list-imports", help="List all imports for the selected GitHub app installation.")
def list_github_imports():
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Collecting GitHub app installations...", total=None)

        result = github_service.get_installations_by_user_id()

        if isinstance(result, GithubAppInstallationHttpResponse):
            progress.stop()
            installation_dict = {f"{installation.id}: {installation.github_account_name}": installation for installation in result.installations}
            installation_choices = [f"{installation.id}: {installation.github_account_name}" for installation in result.installations]

            if result.installations and len(result.installations) > 0:
                action = questionary.select(
                    message="Select an installation:",
                    choices=installation_choices
                ).ask()

                if action is None:
                    raise typer.Exit()

                selected_installation = installation_dict.get(action)

                progress.add_task(description="Fetching repositories...", total=None)
                repositories_response = github_service.get_repositories_for_installation(selected_installation.id)
               
                if repositories_response.repositories:
                    table = Table()
                    table.add_column("Name", justify="left", no_wrap=True)
                    table.add_column("Description", justify="left", no_wrap=True)

                    # Loop through each repository and add data to the table
                    for repo in repositories_response.repositories:
                        table.add_row(
                            repo.github_repository_name,
                            repo.github_repository_description or "No description"
                        )

                    console.print(table)
            else:
                typer.secho(f"No repositories found for the selected installation.", fg=typer.colors.RED)
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
        elif isinstance(result, GeneralErrorResponse):
            typer.secho(f"{result.statusMessage}",
                        fg=typer.colors.RED)
        else:
            progress.stop()
            typer.secho("Unexpected error occurred while fetching GitHub installations.",
                        fg=typer.colors.RED)


@github_app.command(name="uninstall",
                    help="Uninstall the official neptun-github-application onto a repository.")
def uninstall_github_app():
    github_app_url = config_manager.read_config('utils', 'neptun_github_app_url')
    try:
        chrome = webbrowser.get('chrome')
        chrome.open(github_app_url)
        console.print(f"Successfully launched chrome. You are ready to install the neptun-github-application!\nYou can find the installed application here: https://neptun-webui.vercel.app/account")
    except webbrowser.Error:
        typer.secho("Seems like chrome is not installed on your system.\nTo manually add the github-application, please visit: https://github.com/apps/neptun-github-app/installations", fg=typer.colors.RED)
