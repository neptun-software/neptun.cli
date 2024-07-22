import typer
from neptun.cmd.config import config_app
from neptun import __app_name__, __version__

app = typer.Typer()

app.add_typer(config_app, name="config", help=config_app.info.help)
