import questionary
import typer
from rich.console import Console
from neptun.bot.neptunbot import NeptunChatBot

assistant_app = typer.Typer(name="Neptun chatbot", help="Start chatting with the neptun-chatbot.")


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
        console.print(f"Bot: {response}")
        if "bye" in user_input.lower():
            break


@assistant_app.command(name="ask", help="Ask a question to the bot")
def ask(question: str):
    response = bot.respond(question)
    console.print(f"Bot: {response}")
