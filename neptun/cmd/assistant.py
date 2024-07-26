import questionary
import typer
from rich.console import Console
from neptun.bot.neptunbot import NeptunChatBot
from rich.markdown import Markdown

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
        console.print(f"Bot: {response}")
        if "bye" in user_input.lower():
            break


@assistant_app.command(name="ask", help="Ask a question to the bot")
def ask(question: str):
    response = bot.respond(question)

    MARKDOWN = """
# Summary
Here's an example of some Markdown code:

  ```python
    print("Hello, World!")
  ```
Output
Hello, World!
Please note that this will only output text if your browser supports HTML/CSS, as Markdown uses HTML syntax for its formatting. If your browser doesn't support Markdown or CSS, you'll get plain text instead.
Also note that the output of the code above may vary depending on your specific settings. For example, some browsers may display line breaks differently, or the Markdown syntax may not be recognized by all versions of Markdown.
So it's always a good idea to test your Markdown code in multiple browsers and devices to ensure that it looks and works the way you want it to.
    """

    md = Markdown(MARKDOWN)
    console.print(md)

    #console.print(f"Bot: {response}")


