import typer
from neptun.cmd.config import config_app
from neptun.cmd.auth import auth_app
from neptun.cmd.assistant import assistant_app
from neptun import __app_name__, __version__
from neptun.cmd.github import github_app
from neptun.cmd.collection import collection_app
from neptun.cmd.health import health_app
from neptun.cmd.info import info_app
from neptun.cmd.open import open_app
from neptun.cmd.project import project_app
from neptun.cmd.template import template_app

app = typer.Typer()

app.add_typer(config_app, name="config", help=config_app.info.help)
app.add_typer(auth_app, name="auth", help=auth_app.info.help)
app.add_typer(assistant_app, name="assistant", help=assistant_app.info.help)
app.add_typer(collection_app, name="collection", help=collection_app.info.help)
app.add_typer(github_app, name="github", help=github_app.info.help)
app.add_typer(info_app, name="info", help=info_app.info.help)
app.add_typer(open_app, name="open", help=open_app.info.help)
app.add_typer(health_app, name="health", help=health_app.info.help)
app.add_typer(template_app, name="template", help=template_app.info.help)
app.add_typer(project_app, name="project", help=project_app.info.help)

