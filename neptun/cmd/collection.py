import os
from typing import List, Tuple

import typer
import questionary
from rich.console import Console
from rich.table import Table
from concurrent.futures import ThreadPoolExecutor, as_completed
from neptun.model.http_requests import CreateCollectionRequest, UserFile, CreateTemplateRequest, TemplateData
from neptun.utils.services import CollectionService, TemplateService
from neptun.utils.managers import ConfigManager
from rich.progress import Progress, SpinnerColumn, TextColumn
from neptun.model.http_responses import TemplateCollectionResponse, GeneralErrorResponse, Template

collection_app = typer.Typer(name="Collection Manager",
                             help="Manage your neptun collections.")

collection_service = CollectionService()
template_service = TemplateService()
config_manager = ConfigManager()
console = Console()

EXT_TO_LANG = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.cpp': 'C++',
    '.java': 'Java',
    '.html': 'HTML',
    '.css': 'CSS',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.go': 'Go',
    '.sh': 'Shell Script',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.txt': 'Text',
    '.md': 'Markdown',
}


def options():
    choice = questionary.select(
        "Choose an available function:",
        choices=["Create Collection()", "List Collections()", "Delete Collection()"],
    ).ask()

    match choice:
        case "Create Collection()":
            create_template_collection()
        case "List Collection()":
            list_template_collections()
        case "Delete Collection()":
            delete_template_collection()
        case "Inspect Collection()":
            inspect_template_collection()


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
            progress.stop()

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


@collection_app.command(name="inspect", help="Inspect the information about a template collection.")
def inspect_template_collection(limit: int = None, select_last: bool = False):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available collections...", total=None)

        result = collection_service.get_user_template_collections()
        collection_dict = {f"{collection.id}: {collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.id}: {collection.name}" for collection in
                                  (result.collections[:-limit] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.id}: {collection.name}" for collection in
                                  (result.collections[:limit] if limit else result.collections)]

        if isinstance(result, TemplateCollectionResponse):
            progress.update(collecting_data_task, completed=True, visible=False)
            progress.stop()

            if result.collections and len(result.collections) > 0:
                action = questionary.select(
                    message="Select a template collection to inspect:",
                    choices=collection_choices,
                ).ask()

                if action is None:
                    raise typer.Exit()
                selected_collection_object = collection_dict.get(action)
                table = Table()
                table.add_column("Attribute", justify="left", no_wrap=True)
                table.add_column("Value", justify="left", no_wrap=True)

                table.add_row("ID", str(selected_collection_object.id))
                table.add_row("Name", selected_collection_object.name)
                table.add_row("Description", selected_collection_object.description if selected_collection_object.description else '/')
                table.add_row("Share UUID", selected_collection_object.share_uuid)
                table.add_row("Is Shared", "Yes" if selected_collection_object.is_shared else "No")

                console.print(table)

            else:
                typer.secho(f"No collections available!", fg=typer.colors.BRIGHT_YELLOW)


def get_readable_files_in_directory(directory: str, neptun_user_id: int) -> List[UserFile]:
    readable_files = []

    for file_name in os.listdir(directory):

        if file_name == "app.log":
            continue

        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_name_without_extension, file_extension = os.path.splitext(file_name)
                extensions = []

                while file_extension:
                    extensions.insert(0, file_extension)
                    file_name_without_extension, file_extension = os.path.splitext(file_name_without_extension)

                full_extension = ''.join(extensions)

                language = EXT_TO_LANG.get(full_extension.lower(), 'Unknown')

                readable_files.append(UserFile(
                    title=file_name,
                    text=content,
                    language=language,
                    extension=full_extension,
                    neptun_user_id=neptun_user_id
                ))

            except (UnicodeDecodeError, IOError):
                continue

    return readable_files


def process_file(readable_file, latest_collection):
    try:
        typer.secho(f"Processing {readable_file.title}...", fg=typer.colors.BRIGHT_BLACK)

        create_template_data = TemplateData(
            description="No description",
            file_name=f"{readable_file.title}",
            neptun_user_id=int(config_manager.read_config('auth.user', 'id'))
        )

        create_template_request = CreateTemplateRequest(
            template=create_template_data,
            file=readable_file
        )

        create_template_result = template_service.create_template(
            collection_uuid=latest_collection.share_uuid,
            create_template_request=create_template_request,
        )

        if isinstance(create_template_result, Template):
            typer.secho(f"Template '{create_template_result.file_name}' created successfully!", fg=typer.colors.GREEN)
            typer.echo(readable_file.extension)
        elif isinstance(create_template_result, GeneralErrorResponse):
            typer.secho(
                f"Error: {create_template_result.statusMessage} (Status Code: {create_template_result.statusCode})",
                fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"An error occurred while processing {readable_file.title}: {str(e)}", fg=typer.colors.RED)


@collection_app.command(name="create", help="Automatically create a new collection with all the files inside your current directory.")
def auto_create_template_collection(directory: str = typer.Argument(".", help="Directory for the collection")):
    if directory == ".":
        directory = os.getcwd()

    current_directory = os.path.basename(directory)
    typer.secho(f"{current_directory}", fg=typer.colors.GREEN)

    is_basename = questionary.select(
        f"Would you like to customize the collection's name? ({current_directory})",
        choices=["Yes", "No"]
    ).ask()

    name = questionary.text("Name of the template collection:").ask() if is_basename == "Yes" else current_directory

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
            typer.secho(f"Template collection '{create_collection_request.name}' created successfully!",
                        fg=typer.colors.GREEN)

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

            typer.secho(f"Reading files from {current_directory}...", fg=typer.colors.BRIGHT_BLACK)

            readable_files = get_readable_files_in_directory(directory, int(config_manager.read_config('auth.user', 'id')))

            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(process_file, readable_file, latest_collection)
                    for readable_file in readable_files
                ]

                for future in as_completed(futures):
                    pass

            typer.secho(f"Finished appending templates to {latest_collection.name}!", fg=typer.colors.GREEN)
            template_service.close()

        elif isinstance(result, GeneralErrorResponse):
            typer.echo(f"Error: {result.statusMessage} (Status Code: {result.statusCode})")


