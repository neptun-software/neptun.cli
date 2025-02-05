import os

import typer
import questionary
from rich.console import Console
from rich.table import Table
from neptun.model.http_requests import CreateCollectionRequest
from neptun.utils.services import CollectionService
from neptun.utils.managers import ConfigManager
from rich.progress import Progress, SpinnerColumn, TextColumn
from neptun.model.http_responses import TemplateCollectionResponse,GeneralErrorResponse

collection_app = typer.Typer(name="Collection Manager",
                             help="Manage your neptun collections.")

collection_service = CollectionService()
config_manager = ConfigManager()
console = Console()


def options():
    choice = questionary.select(
        "Choose an available function:",
        choices=["Create Template Collection", "List Template Collections", "Delete Template Collection"],
    ).ask()

    match choice:
        case "Create Template Collection()":
            create_template_collection()
        case "List Template Collections()":
            list_template_collections()
        case "Delete Template Collection()":
            delete_template_collection()


@collection_app.command(name="options", help="List all template options available.")
def list_template_options():
    options()


@collection_app.command(name="create-empty", help="Create a new template collection.")
def create_template_collection():

    name = questionary.text("Name of the template collection:").ask()
    is_shared = questionary.select(
        "Should this collection be shared?",
        choices=["Yes", "No"]
    ).ask()
    description = questionary.text("Description for the collection (optional):").ask()

    create_collection_request = CreateCollectionRequest(
        name=name,
        description=description if description else '',
        is_shared=True if is_shared == "Yes" else False,
        neptun_user_id=int(config_manager.read_config('auth.user', 'id'))
    )
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        task = progress.add_task(description="Creating template collection...", total=None)

        result = collection_service.create_template_collection(create_collection_request)

        progress.stop()

        if isinstance(result, TemplateCollectionResponse):
            typer.secho(f"Template collection '{create_collection_request.name}' created successfully!", fg=typer.colors.GREEN)

            latest_collection = result.collections[-1]
            table = Table()
            table.add_column("Attribute", justify="left", no_wrap=True)
            table.add_column("Value", justify="left", no_wrap=True)

            table.add_row("ID", str(latest_collection.id))
            table.add_row("Name", latest_collection.name)
            table.add_row("Description", latest_collection.description if latest_collection.description else '/')
            table.add_row("Share UUID", latest_collection.share_uuid)
            table.add_row("Is Shared", "Yes" if latest_collection.is_shared else "No")

            console.print(table)

        elif isinstance(result, GeneralErrorResponse):
            typer.echo(f"Error: {result.statusMessage} (Status Code: {result.statusCode})")


@collection_app.command(name="list", help="List all template collections.")
def list_template_collections(limit: int = None, select_last: bool = False):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        task = progress.add_task(description="Fetching template collections...", total=None)

        collections_response = collection_service.get_user_template_collections()

        progress.stop()

        if isinstance(collections_response, GeneralErrorResponse):
            console.print(f"[bold red]Error: {collections_response.statusMessage}[/bold red]")
            return

        table = Table()
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Name", justify="left", style="magenta", no_wrap=True)
        table.add_column("Description", justify="left", no_wrap=True)
        table.add_column("Shared", justify="center", style="green", no_wrap=True)

        if select_last:
            collections_to_display = collections_response.collections[-limit:] if limit else collections_response.collections[-1:]
        else:
            collections_to_display = collections_response.collections[:limit] if limit else collections_response.collections

        for collection in collections_to_display:
            table.add_row(
                str(collection.id),
                collection.name,
                collection.description or "No description",
                "Yes" if collection.is_shared else "No",
            )

        console.print(table)


@collection_app.command(name="delete", help="Delete a template collection.")
def delete_template_collection(limit: int = None, select_last: bool = False):
    questionary.text(message="")
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available collections...", total=None)

        result = collection_service.get_user_template_collections()
        collection_dict = {f"{collection.id}: {collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.id}: {collection.name}" for collection in (result.collections[:-limit] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.id}: {collection.name}" for collection in (result.collections[:limit] if limit else result.collections)]

        if isinstance(result, TemplateCollectionResponse):
            progress.update(collecting_data_task, completed=True, visible=False)

            if result.collections and len(result.collections) > 0:
                action = questionary.select(
                    message="Select a template collection to delete:",
                    choices=collection_choices,
                ).ask()

                if action is None:
                    raise typer.Exit()

                selected_collection_object = collection_dict.get(action)

                deleting_data_task = progress.add_task(description="Deleting selected collection...", total=None)

                deleted_collection = collection_service.delete_template_collection(selected_collection_object.share_uuid)
                if deleted_collection is True:
                    progress.update(deleting_data_task, completed=True, visible=False)
                    progress.stop()
                    typer.secho(f"Successfully deleted collection: {selected_collection_object.name}.", fg=typer.colors.GREEN)
                else:
                    typer.secho(f"Failed to delete collection: {selected_collection_object.name}.", fg=typer.colors.RED)
            else:
                typer.secho(f"No collections available!", fg=typer.colors.BRIGHT_YELLOW)


@collection_app.command(name="create", help="Automatically create a new collection with all the files inside your current directory.")
def auto_create_template_collection(directory: str = typer.Argument(".", help="Directory for the collection")):
    if directory == ".":
        directory = os.getcwd()

    current_directory = os.path.basename(directory)
    typer.secho(f"{current_directory}", fg=typer.colors.GREEN)



