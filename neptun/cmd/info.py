import importlib.resources
import typer
from rich.console import Console, Group
import toml
from rich.text import Text
from rich.panel import Panel
import pyfiglet
from colorama import Fore
from colorama import Style

info_app = typer.Typer(name="neptun_status", help="Display the current status and version of the Neptun app.")

console = Console()


def get_project_info():

    with importlib.resources.path('neptun.config', 'info.toml') as neptun_info:
        pyproject = toml.load(neptun_info)

    project_info = {
        "name": pyproject["neptun"]["info"]["name"],
        "version": pyproject["neptun"]["info"]["version"],
        "description": pyproject["neptun"]["info"]["description"],
        "authors": ", ".join(pyproject["neptun"]["info"]["authors"]),
        "license": pyproject["neptun"]["info"]["license"]
    }

    return project_info


@info_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        project_info = get_project_info()

        figlet = pyfiglet.Figlet(font="ansi_regular")
        styled_figlet = Fore.LIGHTWHITE_EX + Style.BRIGHT + figlet.renderText("neptun")

        name_version_text = Text.from_markup(f"[bold blue]{project_info['name']}[/bold blue] [bold yellow]v{project_info['version']}[/bold yellow]", justify="left")
        description_text = Text.from_markup(f"{project_info['description']}", justify="left")
        authors_text = Text.from_markup(f"[bold]Authors:[/bold] [bold yellow]{project_info['authors']}[/bold yellow]", justify="left")
        license_text = Text.from_markup(f"[bold]License:[/bold] [bold yellow]{project_info['license']}[/bold yellow]", justify="left")

        panel = Panel(
            Group(name_version_text, description_text, authors_text, license_text),
            title=Text("Neptun Project Info", style="yellow"),
            border_style="white bold",
            expand=False,
            title_align="center",
        )
        print(styled_figlet, end="")
        console.print(panel)


if __name__ == "__main__":
    info_app()
