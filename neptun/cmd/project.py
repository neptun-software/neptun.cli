import typer
import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.console import Console

from neptun.model.http_requests import CreateNeptunProjectRequest
from neptun.model.http_responses import CreateNeptunProjectResponse, GeneralErrorResponse
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ProjectService


console = Console()
project_app = typer.Typer(name="Neptun-Project Manager",
                          help="Create Neptun projects and interact with them via the CLI-Tool.")

project_service = ProjectService()
config_manager = ConfigManager()


@project_app.command(name="create", help="Create a new Neptun project.")
def create_project():
    name = questionary.text("Project name:").ask()
    description = questionary.text("Project description (optional):").ask()
    project_type_map = {
        "Website (static or dynamic)": "web-site",
        "Microservice, hosted on the internet. (web-service)": "web-service",
        "Multi-Platform App (web-app, desktop-app & mobile-app in one (web-based))": "web-app"
    }

    programming_language_map = {
        "Typescript (recommended)": "typescript",
        "Javascript": "javascript",
        "PHP": "php",
        "Go": "go",
        "Python": "python",
        "Java": "java",
        "Kotlin": "kotlin",
        "Ruby": "ruby",
        "Elixir": "elixir"
    }
    project_type = questionary.select(
        "Select the project type:",
        choices=[
            iterator for iterator in project_type_map.keys()
        ]
    ).ask()

    programming_language = questionary.select(
        "Select the programming language:",
        choices=[
            iterator for iterator in programming_language_map.keys()
        ]
    ).ask()

    project_type_mapped = project_type_map.get(project_type)
    programming_language_mapped = programming_language_map.get(programming_language)

    try:
        create_project_request = CreateNeptunProjectRequest(
            name=name,
            description=description if description else '',
            type=project_type_mapped,
            main_language=programming_language_mapped,
            neptun_user_id=int(config_manager.read_config("auth.user", "id"))
        )
    except Exception:
        console.print("[bold red]Error: User is not authenticated. Please log in.[/bold red]")
        raise typer.Exit()

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        task = progress.add_task(description="Creating Neptun project...", total=None)

        result = project_service.create_project(create_project_request)

        progress.stop()

        if isinstance(result, CreateNeptunProjectResponse):
            typer.secho(f"Neptun project '{create_project_request.name}' created successfully!",
                        fg=typer.colors.GREEN)

            project = result.project
            table = Table()
            table.add_column("Attribute", justify="left", no_wrap=True)
            table.add_column("Value", justify="left", no_wrap=True)

            table.add_row("Name", project.name)
            table.add_row("Description", project.description if project.description else '/')
            table.add_row("Project Type", project.type)
            table.add_row("Programming Language", project.main_language)

            console.print(table)

        elif isinstance(result, GeneralErrorResponse):
            typer.echo(f"Error: {result.statusMessage} (Status Code: {result.statusCode})")
