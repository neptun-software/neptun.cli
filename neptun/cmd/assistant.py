import asyncio
import textwrap
import time
from functools import wraps
import re
import httpx
import questionary
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from neptun.utils.helpers import ChatResponseConverter
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatsHttpResponse, GeneralErrorResponse, ErrorResponse, CreateChatHttpResponse
from neptun.model.http_requests import CreateChatHttpRequest
from neptun.bot.tui import NeptunChatApp
from rich.markdown import Markdown
from rich.table import Table
from io import StringIO

assistant_app = typer.Typer(name="Neptun Chatbot", help="Start chatting with the neptun-chatbot.")

console = Console()
bot = NeptunChatApp()
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


def print_chat_table(chat):
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

    table.add_row(f"{chat.id}",
                  f"{chat.name}",
                  f"{chat.model}",
                  f"{chat.created_at}")

    console.print(table)


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

            typer.secho(f"Successfully created a new chat!",
                        fg=typer.colors.GREEN)

            print_chat_table(result.chat)

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

            if result.chats is not None and len(result.chats) > 0:
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
            else:
                typer.secho(f"No chats available!",
                            fg=typer.colors.BRIGHT_YELLOW)

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
    questionary.text(message="")  # necessary but don't know why -> bug appears when running `neptun assistant delete` if non-existent
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

            if result.chats is not None and len(result.chats) > 0:
                action = questionary.select(
                    message="Select an available chat:",
                    choices=chat_choices,
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
            else:
                typer.secho(f"No chats available!",
                            fg=typer.colors.BRIGHT_YELLOW)


def chat():
    bot.run()


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
            enter_available_chats_dialog()
        case "List Chats()":
            list_available_chats()
        case "Delete Chat()":
            delete_selected_chat_dialog()


@assistant_app.command(name="list", help="List all available ai chat-dialogs.")
def list_chats():
    list_available_chats()


@assistant_app.command(name="enter", help="List and automatically enter a chat-dialog.")
def enter_chat():
    enter_available_chats_dialog()


@assistant_app.command(name="delete", help="List and delete a chat-dialog.")
def delete_chat():
    delete_selected_chat_dialog()


@assistant_app.command(name="create", help="Create a new chat-dialog.")
def create_chat():
    create_new_chat_dialog()

'''
@assistant_app.command(name="ask", help="Ask a question to the bot")
def ask(question: str):
    response = bot.respond(question)
    if response.startswith("markdown:"):
        markdown_content = response[len("markdown:"):].strip()
        print_markdown_stream(markdown_content)
    else:
        console.print(f"Bot: {response}")
'''


async def print_markdown_stream(markdown_content: str):
    """Render markdown content line by line from a text stream."""
    markdown_stream = StringIO(markdown_content)
    for line in markdown_stream:
        md = Markdown(line)
        console.print(md)
        await asyncio.sleep(0.5)


def extract_message_parts(raw_message):
    segments = re.findall(r'0:"(.*?)"', raw_message)

    return segments


def extract_markdown_content(message_parts):
    try:
        start_index = message_parts.index('```') + 2
        end_index = message_parts.index('```', start_index)
    except ValueError:
        return ""

    markdown_content = message_parts[start_index:end_index]

    return ''.join(markdown_content).replace('\\n', '\n')


def pretty_print(message):
    wrapper = textwrap.TextWrapper(width=50)  # Adjust the width as needed
    wrapped_text = wrapper.fill(text=message)
    print(wrapped_text, end="")


chat_response_converter = ChatResponseConverter("")


async def handle_chunk(message):
    print("Raw Message:")
    print(message)

    print(chat_response_converter.extract_sections())

    # Clean up unwanted characters from the message
    cleaned_message = re.sub(r'^\d+:"', '', message)
    cleaned_message = re.sub(r'"\n$', '', cleaned_message)
    cleaned_message = re.sub(r'"\n', '', cleaned_message)
    cleaned_message = re.sub(r'(\d+):"', '', cleaned_message)

    cleaned_message = re.sub(r'\s+', ' ', cleaned_message)

    return "extract_markdown_content(markdown_content)"


async def stream():
    url = "https://neptun-webui.vercel.app/api/ai/huggingface/OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5/chat?chat_id=12"
    cookies = {
        'neptun-session': 'Fe26.2**f60792516417ab438160034a2391ee21ef396cc52ec30bb39cf03bbafe94b6b0*kBsI65Kp1WURJ1vNgBGlXQ*eBJljqwD52UypEye17yvc_mZxO9MWyOUK-6bsjMhTd6VY4YBhsfrdUepG_jeWC0wXcOjAc1VV3Gav3daXkdmxRfpLIsqa5AvrtWI-UEBi8CHvHV9WXXYNvXUpyBqPQt3FZj9w1SzyE_CDV52_ybsQXo4KMDJ152wMm5TG2X-MixMYnRwg2hPDeALk1jOqOBXo31Ma9GOeZsqYiPxK4fPNERUImrDm5D8qTiEvVyTu2w**29ad72d75f56124b0fc63f707c2f8676079820b461d478a31bd0b644456d5a5a*qLGyVt7-8nrRv6-QJjzQiNXC4HQi9-6GSOfy-217DIQ'
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": "write me a hello world in markdown!"
            }
        ],
    }

    with httpx.Client(cookies=cookies) as client:

        async with client.stream('POST', url=url, json=data) as resp:
            async for chunk in resp.aiter_bytes():
                buffer += chunk
        message = buffer.decode('utf-8')
        await cb(message)


async def main():
    markdown = await stream(handle_chunk)
    print(markdown)


if __name__ == "__main__":
    asyncio.run(main())
