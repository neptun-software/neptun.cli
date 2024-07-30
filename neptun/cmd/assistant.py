import asyncio
from functools import wraps
import questionary
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from neptun.bot.neptunbot import NeptunChatBot
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatsResponse, GeneralErrorResponse
from rich.markdown import Markdown
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


@assistant_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        chat()


@ensure_authenticated
def chat():

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
    ) as progress:
        progress.add_task(description="Collecting available chats...",
                          total=None)

        result = asyncio.run(chat_service.get_available_ai_chats())

        questions = [
            {
                "type": "select",
                "name": "select_chat",
                "message": "Select an available chat:",
                "choices": [chat.name for chat in result.chats] if result.chats else ["Create a new chat"],
            },
            {
                "type": "text",
                "name": "name_new_chat",
                "message": "Name the chat:",
                "when": lambda x: x["select_chat"] == "Create a new chat",
            },
            {
                "type": "select",
                "name": "select_new_chat_model",
                "message": "Select a ai-base-model:",
                "when": lambda x: x["name_new_chat"],
                "choices": ["OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5",
                            "mistralai/Mistral-7B-Instruct-v0.1"],
            }
        ]

        if isinstance(result, ChatsResponse):
            progress.stop()

            prompt_data = prompt(questions)

        elif isinstance(result, GeneralErrorResponse):
            print(result.statusMessage)

    '''
    console.print("Chat bot started! Type 'bye' to exit.\n")
    while True:
        user_input = questionary.text(""You:").ask()
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
    '''


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
