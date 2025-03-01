import typer
import questionary
from rich.console import Console
from rich.table import Table
import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn
from neptun.model.http_responses import GeneralErrorResponse
from neptun.utils.services import TemplateService, CollectionService

template_app = typer.Typer(name="Template Manager",
                           help="Add your templates to your personal Neptun-Collections.")

template_service = TemplateService()
collection_service = CollectionService()
console = Console()


@template_app.command(name="delete", help="Delete a template from a collection.")
def delete_template(
    limit: int = typer.Option(None, "--limit", "-l", help="Limit the number of collections displayed"),
    select_last: bool = typer.Option(False, "--select-last", "-s", help="Display the last collections instead of the first ones")
):
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Collecting available collections...", total=None)
        collections_result = collection_service.get_user_template_collections()
        progress.stop()

    if isinstance(collections_result, GeneralErrorResponse):
        console.print(f"[bold red]Error: {collections_result.statusMessage}[/bold red]")
        raise typer.Exit()

    if not collections_result.collections:
        console.print("[bold yellow]No collections available![/bold yellow]")
        raise typer.Exit()

    collection_dict = {collection.name: collection for collection in collections_result.collections}
    if select_last:
        collection_choices = [collection.name for collection in (collections_result.collections[-limit:] if limit else collections_result.collections[-1:])]
    else:
        collection_choices = [collection.name for collection in (collections_result.collections[:limit] if limit else collections_result.collections)]

    selected_collection_name = questionary.select(
        "Select a template collection:",
        choices=collection_choices
    ).ask()

    if not selected_collection_name:
        raise typer.Exit()

    selected_collection = collection_dict[selected_collection_name]

    if not selected_collection.templates or len(selected_collection.templates) == 0:
        console.print("[bold yellow]No templates available in the selected collection![/bold yellow]")
        raise typer.Exit()

    template_dict = {
        f"{template.get("file_name")}": template
        for template in selected_collection.templates
    }
    template_choices = list(template_dict.keys())
    selected_template_str = questionary.select(
        "Select a template to delete:",
        choices=template_choices,
    ).ask()

    if not selected_template_str:
        raise typer.Exit()

    selected_template = template_dict[selected_template_str]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("Deleting selected template...", total=None)
        deletion_result = template_service.delete_template(selected_collection.id, int(selected_template.get("id")))
        progress.stop()

    if deletion_result is True:
        console.print(
            f"[bold green]Successfully deleted template: {selected_template.get("file_name")} from collection {selected_collection.name}.[/bold green]"
        )
    else:
        console.print(
            f"[bold red]Failed to delete template: {selected_template.get("file_name")}. Reason: {deletion_result.statusMessage}[/bold red]"
        )
