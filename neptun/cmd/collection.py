import os
import random
from collections import deque
from pathlib import Path
from typing import List, Tuple

import typer
import questionary
from rich.console import Console
from rich.table import Table
from concurrent.futures import ThreadPoolExecutor, as_completed
from neptun.model.http_requests import CreateCollectionRequest, UserFile, CreateTemplateRequest, TemplateData, \
    UpdateCollectionRequest
from neptun.utils.dicts import EXT_TO_LANG
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


@collection_app.command(name="options", help="List all template options available.")
def options():
    choice = questionary.select(
        "Choose an available function:",
        choices=["Create Collection()",
                 "List Collections()",
                 "Delete Collection()",
                 "Update Collection()",
                 "Pull Collection()"],
    ).ask()

    match choice:
        case "Create Collection()":
            create_template_collection()
        case "List Collections()":
            list_template_collections()
        case "Delete Collection()":
            delete_template_collection()
        case "Inspect Collection()":
            inspect_template_collection()
        case "Update Collection()":
            update_template_collection()
        case "Pull Collection()":
            pull_template_collection()


@collection_app.command(name="create-empty", help="Create a new template collection.")
def create_template_collection():
    name = questionary.text("Name of the template collection:").ask()
    is_shared = questionary.select(
        "Should this collection be shared?",
        choices=["Yes", "No"]
    ).ask()
    description = questionary.text("Description for the collection (optional):").ask()

    try:
        create_collection_request = CreateCollectionRequest(
            name=name,
            description=description if description else '',
            is_shared=True if is_shared == "Yes" else False,
            neptun_user_id=int(config_manager.read_config('auth.user', 'id'))
        )
    except Exception as e:
        console.print(f"[bold red]Error: User is not authenticated. Please log in.[/bold red]")
        raise typer.Exit()

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
        table.add_column("Name", justify="left", style="magenta", no_wrap=True)
        table.add_column("Description", justify="left", no_wrap=True)
        table.add_column("Shared", justify="center", style="green", no_wrap=True)
        table.add_column("Shared-UUID", justify="center", style="green", no_wrap=True)

        if select_last:
            collections_to_display = collections_response.collections[
                                     -limit:] if limit else collections_response.collections[-1:]
        else:
            collections_to_display = collections_response.collections[
                                     :limit] if limit else collections_response.collections

        for collection in collections_to_display:
            table.add_row(
                collection.name,
                collection.description or "No description",
                "Yes" if collection.is_shared else "No",
                collection.share_uuid,

            )

        console.print(table)


@collection_app.command(name="list-shared", help="List all shared template collections.")
def list_shared_template_collections(
    limit: int = typer.Option(None, "--limit", "-l", help="Limit the number of shared collections displayed"),
    select_last: bool = typer.Option(False, "--select-last", "-s", help="Display the last shared collections instead of the first ones")
):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching shared template collections...", total=None)
        shared_response = collection_service.get_shared_collections()
        progress.stop()

        if isinstance(shared_response, GeneralErrorResponse):
            console.print(f"[bold red]Error: {shared_response.statusMessage}[/bold red]")
            return

        table = Table()
        table.add_column("Name", justify="left", style="magenta", no_wrap=True)
        table.add_column("Description", justify="left")
        table.add_column("Shared", justify="center", style="green", no_wrap=True)
        table.add_column("Shared-UUID", justify="center", style="green", no_wrap=True)

        if select_last:
            collections_to_display = shared_response.collections[-limit:] if limit else shared_response.collections[-1:]
        else:
            collections_to_display = shared_response.collections[:limit] if limit else shared_response.collections

        for collection in collections_to_display:
            table.add_row(
                collection.name,
                collection.description or "No description",
                "Yes" if collection.is_shared else "No",
                collection.share_uuid,
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
        collection_dict = {f"{collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:-limit] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:limit] if limit else result.collections)]

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

                deleted_collection = collection_service.delete_template_collection(
                    selected_collection_object.id)
                if deleted_collection is True:
                    progress.update(deleting_data_task, completed=True, visible=False)
                    progress.stop()
                    typer.secho(f"Successfully deleted collection: {selected_collection_object.name}.",
                                fg=typer.colors.GREEN)
                else:
                    typer.secho(f"Failed to delete collection: {selected_collection_object.name}.", fg=typer.colors.RED)
            else:
                typer.secho(f"No collections available!", fg=typer.colors.BRIGHT_YELLOW)


@collection_app.command(name="update", help="Update a template collection.")
def update_template_collection(limit: int = None, select_last: bool = False):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available collections...", total=None)

        result = collection_service.get_user_template_collections()

        if isinstance(result, GeneralErrorResponse):
            typer.secho(f"Error fetching collections: {result.statusMessage}", fg=typer.colors.RED)
            return

        collection_dict = {f"{collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[-limit:] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:limit] if limit else result.collections)]

        progress.update(collecting_data_task, completed=True, visible=False)
        progress.stop()

        if not result.collections:
            typer.secho("No collections available!", fg=typer.colors.BRIGHT_YELLOW)
            return

        action = questionary.select(
            message="Select a template collection to update:",
            choices=collection_choices,
        ).ask()

        selected_collection_object = collection_dict.get(action)

        should_update_name = questionary.select(
            "Would you like to update the name?",
            choices=["Yes", "No"]
        ).ask()

        name = questionary.text(
            "Update name of the template collection:").ask() if should_update_name == "Yes" else selected_collection_object.name

        should_update_description = questionary.select(
            "Would you like to update the description?",
            choices=["Yes", "No"]
        ).ask()

        description = questionary.text(
            "Update description of the template collection:").ask() if should_update_description == "Yes" else selected_collection_object.description

        should_update_shared = questionary.select(
            "Would you like to update the share-status?",
            choices=["Yes", "No"]
        ).ask()

        is_shared = selected_collection_object.is_shared
        if should_update_shared == "Yes":
            share_status = questionary.select(
                "Should this collection be shared?",
                choices=["Yes", "No"]
            ).ask()
            is_shared = True if share_status == "Yes" else False

        update_collection_request = UpdateCollectionRequest(
            name=name,
            description=description,
            is_shared=is_shared,
            neptun_user_id=selected_collection_object.neptun_user_id
        )

        typer.secho(f"Updating collection: {name}...", fg=typer.colors.BRIGHT_BLACK)

        response = collection_service.update_template_collection(
            id=selected_collection_object.id,
            update_request=update_collection_request)

        if isinstance(response, GeneralErrorResponse):
            typer.secho(f"Failed to update collection: {response.statusMessage}", fg=typer.colors.RED)
        else:
            typer.secho(f"Successfully updated collection: {name}.", fg=typer.colors.GREEN)


@collection_app.command(name="inspect", help="Inspect the information about a template collection.")
def inspect_template_collection(limit: int = None, select_last: bool = False):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available collections...", total=None)

        result = collection_service.get_user_template_collections()
        collection_dict = {f"{collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:-limit] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.name}" for collection in
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

                table.add_row("Name", selected_collection_object.name)
                table.add_row("Description",
                              selected_collection_object.description if selected_collection_object.description else '/')
                table.add_row("Share UUID", selected_collection_object.share_uuid)
                table.add_row("Is Shared", "Yes" if selected_collection_object.is_shared else "No")

                console.print(table)

            else:
                typer.secho(f"No collections available!", fg=typer.colors.BRIGHT_YELLOW)


# think smart... not hard...
def extract_filename_and_extension(file_name: str) -> Tuple[str, str]:
    if file_name.startswith("."):
        temp_name = "dummy" + file_name  # replace non-existing filename with dummy, to ensure that Path().suffixes works
        file_path = Path(temp_name)
    else:
        file_path = Path(file_name)

    suffixes = file_path.suffixes
    filename = file_path.stem.replace("dummy", '')

    if file_name.startswith(".") and '.' in file_name[1:]:
        filename = ""
        full_extension = file_name[file_name.index('.'):]
    else:
        full_extension = "".join(suffixes) if suffixes else ""

    return filename, full_extension


def get_readable_files_in_directory(directory: str, neptun_user_id: int) -> List[UserFile]:
    readable_files = []

    for file_name in os.listdir(directory):
        if file_name == "app.log":
            continue  # Skip log files

        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                filename, full_extension = extract_filename_and_extension(file_name)

                language = EXT_TO_LANG.get(full_extension.lower()[1:], 'Unknown')

                readable_files.append(UserFile(
                    title=f"{full_extension}" if filename == "" else f"{filename}{full_extension}",
                    text=content,
                    language=language,
                    extension=full_extension[1:],
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
            collection_id=latest_collection.id,
            create_template_request=create_template_request,
        )

        if isinstance(create_template_result, Template):
            typer.secho(f"Template '{create_template_result.file_name}' created successfully!", fg=typer.colors.GREEN)
        elif isinstance(create_template_result, GeneralErrorResponse):
            typer.secho(
                f"Error: {create_template_result.statusMessage} (Status Code: {create_template_result.statusCode})",
                fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"An error occurred while processing {readable_file.title}: {str(e)}", fg=typer.colors.RED)


@collection_app.command(name="create",
                        help="Automatically create a new collection with all the files inside your current directory.")
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

    try:
        create_collection_request = CreateCollectionRequest(
            name=name,
            description=description if description else '',
            is_shared=True if is_shared == "Yes" else False,
            neptun_user_id=int(config_manager.read_config('auth.user', 'id'))
        )
    except Exception as e:
        console.print(f"[bold red]Error: User is not authenticated. Please log in.[/bold red]")
        raise typer.Exit()

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

            table.add_row("Name", latest_collection.name)
            table.add_row("Description", latest_collection.description if latest_collection.description else '/')
            table.add_row("Share UUID", latest_collection.share_uuid)
            table.add_row("Is Shared", "Yes" if latest_collection.is_shared else "No")

            console.print(table)

            typer.secho(f"Reading files from {current_directory}...", fg=typer.colors.BRIGHT_BLACK)

            readable_files = get_readable_files_in_directory(directory,
                                                             int(config_manager.read_config('auth.user', 'id')))

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


@collection_app.command(name="pull", help="Pull a template collection from Neptun to your local disk.")
def pull_template_collection(limit: int = None,
                             select_last: bool = False,
                             no_dir: bool = typer.Option(False, "--no-dir",
                                                         help="Place files directly in the current directory without creating a collection folder.")
                             ):
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available collections...", total=None)

        result = collection_service.get_user_template_collections()
        collection_dict = {f"{collection.name}": collection for collection in result.collections}

        if select_last:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:-limit] if limit else result.collections[-1:])]
        else:
            collection_choices = [f"{collection.name}" for collection in
                                  (result.collections[:limit] if limit else result.collections)]

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
                if selected_collection_object:
                    typer.secho(f"Pulling collection: {selected_collection_object.name}", fg="green")
                    save_collection_to_disk(selected_collection_object, no_dir)
                else:
                    typer.secho("Collection not found!", fg="red")
                    raise typer.Exit()


def generate_default_name():
    random_suffix = random.randint(1000, 9999)
    return f"neptun_collection_{random_suffix}"


def save_collection_to_disk(collection, no_dir: bool):
    base_dir = Path(os.getcwd())

    if no_dir:
        collection_dir = base_dir
    else:
        collection_name = collection.name.strip() if collection.name.strip() else generate_default_name()
        collection_dir = base_dir / collection_name
        collection_dir.mkdir(parents=True, exist_ok=True)

    def write_file(template):
        file_path = collection_dir / template["file_name"]
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template["text"])
            typer.secho(f"✔ Created file: {file_path}", fg="blue")
        except IOError as e:
            typer.secho(f"❌ Failed to write file {file_path}: {e}", fg="red")

    with ThreadPoolExecutor() as executor:
        executor.map(write_file, collection.templates)

    typer.secho(
        f"✅ Successfully pulled {collection.name if collection.name.strip() else collection_dir.name} into {'current directory' if no_dir else collection_dir}",
        fg="green"
    )


if __name__ == "__main__":
    test_directory = "test_dir"
    os.makedirs(test_directory, exist_ok=True)

    test_files = {
        ".env.example": 'NAME="helloworld"',
        ".env": 'NAME="helloworld"',
        "hello.env.example": 'NAME="helloworld"',
        "Dockerfile": 'NAME="helloworld"',
        "docker-compose.yaml": 'NAME="helloworld"',
    }

    for file_name, content in test_files.items():
        with open(os.path.join(test_directory, file_name), 'w') as f:
            f.write(content)

    readable_files = get_readable_files_in_directory(test_directory, neptun_user_id=123)

    for file in readable_files:
        print(file)
