from rich.console import Console
import typer
from typing_extensions import Annotated
from neptun import ERRORS
from neptun.utils.config_parser import ConfigManager


console = Console()
config_manager = ConfigManager()


config_app = typer.Typer(name="Authentication Manager", help="This tool allows you to manage and configure general "
                                                          "settings for your application with ease. You can add new "
                                                          "configurations, remove existing ones.")
