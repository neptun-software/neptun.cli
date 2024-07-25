import time

from rich.console import Console
import typer
from typing_extensions import Annotated
from neptun.utils.managers import AuthenticationManager, PostManager
from rich.prompt import Prompt
import re
import questionary
from secrets import compare_digest
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()
authentication_manager = AuthenticationManager()
post_manager = PostManager()

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')


def is_valid(email):
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
    name = Prompt.ask("Enter your name")
    email = Prompt.ask("Enter your email")
    password = Prompt.ask("Enter your password", password=True)
    retype_password = Prompt.ask("Retype your password", password=True)
    if compare_digest(password, retype_password):
        print("Passwords do not match!")
        return
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")


auth_app.command(name="register", help="Register interactively")(register_prompt)


def register(
    name: Annotated[str, typer.Option("--name", prompt=True, help="Full name of the user")],
    email: Annotated[str, typer.Option("--email", prompt=True, help="Email address for registration")],
    password: Annotated[str, typer.Option("--password", prompt=True, help="Password for registration", hide_input=True)],
    retype_password: Annotated[str, typer.Option("--retype-password", prompt=True, help="Retype the password for confirmation", hide_input=True)]
):
    if compare_digest(password, retype_password):
        print("Passwords do not match!")
        return
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")


auth_app.command(name="register-args", help="Register using command-line arguments")(register)


def get_posts():
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Fetching...", total=None)
            posts = post_manager.get_posts()
            progress.update(task, description="Preparing...")
            for post in posts:
                print(post.id)
    except Exception as e:
        print(f"An error occurred: {e}")


auth_app.command(name="posts", help="Test")(get_posts)
