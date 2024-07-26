import asyncio
import time

from rich.console import Console
import typer
from typing_extensions import Annotated
from neptun.model.http_requests import SignUpHttpRequest
from neptun.model.http_responses import SignUpResponse, ErrorResponse
from neptun.utils.services import AuthenticationService
import re
import questionary
from secrets import compare_digest
from neptun.utils.managers import ConfigManager
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from rich.table import Table

console = Console()
authentication_service = AuthenticationService()
config_manager = ConfigManager()


regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')


def is_valid(email):
    if email is None:
        raise typer.Exit()
    if re.fullmatch(regex, email):
        return True
    else:
        return False


auth_app = typer.Typer(name="Authentication Manager",
                       help="This tool is allows you to directly connect the neptun-web-client.")


def login_prompt():

    email = questionary.text("Enter your email:").ask()

    if is_valid(email):
        print(f"Email: {email}")
    else:
        raise typer.Abort

    password = questionary.password("Enter your password:").ask()
    print(f"Password: {'*' * len(password)}")


auth_app.command(name="login", help="Log in interactively")(login_prompt)


def login(
    email: Annotated[str, typer.Option("--email", help="Email address for login")],
    password: Annotated[str, typer.Option("--password", help="Password for login", prompt=True, hide_input=True)]
):

    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")


auth_app.command(name="login-args", help="Log in with command-line arguments")(login)


def register_prompt():

    email = questionary.text("Enter your email:").ask()

    if not is_valid(email):
        typer.secho(f"Invalid email-format!", fg=typer.colors.RED)
        raise typer.Exit()

    password = questionary.password("Enter your password:").ask()

    if password is None:
        raise typer.Exit()

    retype_password = questionary.password("Retype your password:").ask()

    if retype_password is None:
        raise typer.Exit()

    if not compare_digest(password, retype_password):
        typer.secho(f"Passwords do not match!", fg=typer.colors.RED)
        raise typer.Exit()

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Trying to register...", total=None)

        signup_http_request = SignUpHttpRequest(email=email, password=password)

        result = asyncio.run(authentication_service.sign_up(sign_up_http_request=signup_http_request))

        console.print("\n")
        if isinstance(result, SignUpResponse):
            config_manager.update_authentication(id=result.user.id, email=result.user.email, session_cookie=result.session_cookie)
            typer.secho(f"Successfully signed up!", fg=typer.colors.GREEN)
        elif isinstance(result, ErrorResponse):
            if result.data:
                table = Table()
                table.add_column(f"Issue: {result.statusCode} - {result.statusMessage}", justify="left", style="red", no_wrap=True)
                for issue in result.data.issues:
                    table.add_row(f"{issue.message}")

                console.print(table)
            else:
                typer.secho(f"Issue: {result.statusCode} - {result.statusMessage}: Email address already exists!", fg=typer.colors.RED)


auth_app.command(name="register", help="Register interactively")(register_prompt)


def register(
    email: Annotated[str, typer.Option("--email", prompt=True, help="Email address for registration")],
    password: Annotated[str, typer.Option("--password", prompt=True, help="Password for registration", hide_input=True)]
):

    if not is_valid(email):
        typer.secho(f"Invalid email-format!", fg=typer.colors.RED)
        return


auth_app.command(name="register-args", help="Register using command-line arguments")(register)

