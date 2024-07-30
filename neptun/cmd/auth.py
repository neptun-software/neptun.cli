import typer
from neptun.model.http_requests import SignUpHttpRequest, LoginHttpRequest
from neptun.model.http_responses import SignUpHttpResponse, ErrorResponse, LoginHttpResponse
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


def login():

    email = questionary.text("Enter your email:").ask()

    if not is_valid(email):
        typer.secho(f"Invalid email-format!", fg=typer.colors.RED)
        raise typer.Exit()

    password = questionary.password("Enter your password:").ask()

    if password is None:
        raise typer.Exit()

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Trying to login...",
                          total=None)

        login_http_request = LoginHttpRequest(email=email,
                                              password=password)

        result = authentication_service.login(login_up_http_request=login_http_request)

        progress.stop()

        if isinstance(result, LoginHttpResponse):
            config_manager.update_authentication(id=result.user.id,
                                                 email=result.user.email,
                                                 session_cookie=result.session_cookie)
            typer.secho(f"Logged in successfully!", fg=typer.colors.GREEN)
        elif isinstance(result, ErrorResponse):
            if result.data:
                table = Table()
                table.add_column(f"Issue: {result.statusCode} - {result.statusMessage}",
                                 justify="left",
                                 style="red",
                                 no_wrap=True)
                for issue in result.data.issues:
                    table.add_row(f"{issue.message}")

                console.print(table)
            else:
                typer.secho(f"Issue: {result.statusCode} - {result.statusMessage}",
                            fg=typer.colors.RED)


auth_app.command(name="login",
                 help="Log in interactively")(login)


def register():

    email = questionary.text("Enter your email:").ask()

    if not is_valid(email):
        typer.secho(f"Invalid email-format!",
                    fg=typer.colors.RED)
        raise typer.Exit()

    password = questionary.password("Enter your password:").ask()

    if password is None:
        raise typer.Exit()

    retype_password = questionary.password("Retype your password:").ask()

    if retype_password is None:
        raise typer.Exit()

    if not compare_digest(password, retype_password):
        typer.secho(f"Passwords do not match!",
                    fg=typer.colors.RED)
        raise typer.Exit()

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Trying to register...",
                          total=None)

        signup_http_request = SignUpHttpRequest(email=email,
                                                password=password)

        result = authentication_service.sign_up(sign_up_http_request=signup_http_request)

        progress.stop()
        if isinstance(result, SignUpHttpResponse):
            config_manager.update_authentication(id=result.user.id,
                                                 email=result.user.email,
                                                 session_cookie=result.session_cookie)
            typer.secho(f"Successfully signed up!",
                        fg=typer.colors.GREEN)
        elif isinstance(result, ErrorResponse):
            if result.data:
                table = Table()
                table.add_column(f"Issue: {result.statusCode} - {result.statusMessage}",
                                 justify="left", style="red",
                                 no_wrap=True)
                for issue in result.data.issues:
                    table.add_row(f"{issue.message}")

                console.print(table)
            else:
                typer.secho(f"Issue: {result.statusCode} - {result.statusMessage}: Email address already exists!",
                            fg=typer.colors.RED)


auth_app.command(name="register",
                 help="Register interactively")(register)
