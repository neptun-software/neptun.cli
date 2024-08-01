import asyncio
import re
from functools import wraps

import questionary
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from neptun.bot.neptunbot import NeptunChatBot
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatsHttpResponse, GeneralErrorResponse, ErrorResponse, CreateChatHttpResponse
from neptun.model.http_requests import CreateChatHttpRequest
from rich.markdown import Markdown
from rich.table import Table
from io import StringIO
from questionary import prompt, Separator

assistant_app = typer.Typer(name="Neptun Chatbot", help="Start chatting with the neptun-chatbot.")


console = Console()
bot = NeptunChatBot()
chat_service = ChatService()
config_manager = ConfigManager()


def ensure_authenticated(method):
    @wraps(method)
    def wrapper(*args, **kwargs):

        id = config_manager.read_config(section='auth.user', key='id')
        neptun_session_token = config_manager.read_config(section='auth', key='neptun_session_cookie')

        if neptun_session_token is None or id is None:
            raise

        return method(*args, **kwargs)
    return wrapper


# will automatically start a chat based on the config-files latest id
@assistant_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        chat()


def create_new_chat_dialog():
    new_chat_name = questionary.text(
        message="Name the chat:"
    ).ask()

    if new_chat_name is None:
        raise typer.Exit()

    new_chat_model = questionary.select(message="Select a ai-base-model:",
                                        choices=["OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5",
                                                 "mistralai/Mistral-7B-Instruct-v0.1"]).ask()

    if new_chat_model is None:
        raise typer.Exit()

    create_chat_http_request = CreateChatHttpRequest(name=new_chat_name, model=new_chat_model)

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Creating new chat...",
                          total=None)

        result = chat_service.create_chat(create_chat_http_request=create_chat_http_request)

        progress.stop()
        if isinstance(result, CreateChatHttpResponse):
            typer.secho(f"Successfully created a chat!",
                        fg=typer.colors.GREEN)
            config_manager.update_active_chat(id=result.chat.id,
                                              name=result.chat.name,
                                              model=result.chat.model)
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


def enter_available_chats_dialog():
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Collecting available chats...",
                          total=None)

        result = chat_service.get_available_ai_chats()
        chat_dict = {f"{chat.id}: {chat.name}:[{chat.model}]": chat for chat in result.chats}
        chat_choices = [f"{chat.id}: {chat.name}:[{chat.model}]" for chat in result.chats[:5]]

        if isinstance(result, ChatsHttpResponse):
            progress.stop()

            action = questionary.select(
                message="Select an available chat:",
                choices=chat_choices
            ).ask()

            if action is None:
                raise typer.Exit()

            selected_chat_object = chat_dict.get(action)

            config_manager.update_active_chat(id=selected_chat_object.id,
                                              name=selected_chat_object.name,
                                              model=selected_chat_object.model)
            typer.secho(f"Successfully selected: {selected_chat_object.name}!",
                        fg=typer.colors.GREEN)

        elif isinstance(result, GeneralErrorResponse):
            print(result.statusMessage)


def list_available_chats():
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Collecting available chats...",
                          total=None)

        result = chat_service.get_available_ai_chats()

        if isinstance(result, ChatsHttpResponse):
            progress.stop()
            table = Table()
            table.add_column(f"Id",
                             justify="left",
                             no_wrap=True)
            table.add_column(f"Name",
                             justify="left",
                             no_wrap=True)
            table.add_column(f"Model",
                             justify="left",
                             no_wrap=True)
            table.add_column(f"Created At",
                             justify="left",
                             no_wrap=True)

            for iterator in result.chats:
                table.add_row(f"{iterator.id}",
                              f"{iterator.name}",
                              f"{iterator.model}",
                              f"{iterator.created_at}")
            console.print(table)

        elif isinstance(result, GeneralErrorResponse):
            print(result.statusMessage)


def delete_selected_chat_dialog():
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        collecting_data_task = progress.add_task(description="Collecting available chats...",
                          total=None)

        result = chat_service.get_available_ai_chats()
        chat_dict = {f"{chat.id}: {chat.name}:[{chat.model}]": chat for chat in result.chats}
        chat_choices = [f"{chat.id}: {chat.name}:[{chat.model}]" for chat in result.chats[:5]]

        if isinstance(result, ChatsHttpResponse):
            progress.update(collecting_data_task, completed=True, visible=False)

            action = questionary.select(
                message="Select an available chat:",
                choices=chat_choices
            ).ask()

            if action is None:
                raise typer.Exit()

            selected_chat_object = chat_dict.get(action)

            deleting_data_task = progress.add_task(description="Deleting selected chat...",
                              total=None)

            deleted_chat = chat_service.delete_selected_chat(selected_chat_object.id)

            if deleted_chat is True:
                progress.update(deleting_data_task, completed=True, visible=False)
                progress.stop()
                typer.secho(f"Successfully deleted chat: {selected_chat_object.name}.", fg=typer.colors.GREEN)
            else:
                typer.secho(f"Failed to delete chat: {selected_chat_object.name}.", fg=typer.colors.RED)


def chat():
    console.print("Chat bot started! Type 'bye' to exit.\n")
    while True:
        user_input = questionary.text("You:").ask()
        if not user_input:
            continue
        response = bot.respond(user_input)
        if response.startswith("markdown:"):
            markdown_content = response[len("markdown:"):].strip()
            asyncio.run(print_markdown_stream(markdown_content))
        else:
            console.print(f"Bot: {response}")
        if "bye" in user_input.lower():
            break


@assistant_app.command(name="options", help="Open up all options available.")
def options():
    choice = questionary.select(
        "Choose an available function:",
        choices=["Enter Chat()", "New Chat()", "List Chats()", "Delete Chat()"],
    ).ask()

    match choice:
        case "New Chat()":
            create_new_chat_dialog()
        case "Enter Chat()":
            enter_available_chats_dialog()()
        case "List Chats()":
            list_available_chats()
        case "Delete Chat()":
            delete_selected_chat_dialog()


@assistant_app.command(name="ask", help="Ask a question to the bot")
def ask(question: str):
    response = bot.respond(question)
    if response.startswith("markdown:"):
        markdown_content = response[len("markdown:"):].strip()
        print_markdown_stream(markdown_content)
    else:
        console.print(f"Bot: {response}")


async def print_markdown_stream(markdown_content: str):
    """Render markdown content line by line from a text stream."""
    markdown_stream = StringIO(markdown_content)
    for line in markdown_stream:
        md = Markdown(line)
        console.print(md)
        await asyncio.sleep(0.5)
