import asyncio

import questionary
import typer
from rich.console import Console
from neptun.bot.neptunbot import NeptunChatBot
from rich.markdown import Markdown
from io import StringIO


assistant_app = typer.Typer(name="Neptun Chatbot", help="Start chatting with the neptun-chatbot.")


console = Console()
bot = NeptunChatBot()


@assistant_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        chat()


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




