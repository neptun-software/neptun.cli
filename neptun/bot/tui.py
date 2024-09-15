import asyncio
import traceback

from rich.progress import Progress, SpinnerColumn, TextColumn
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Container
from textual.widgets import Footer, Header, Input, Button, Static
from textual.widget import Widget
from textual.widgets import Markdown
from pathlib import Path
from neptun.bot.chat import Conversation
import logging


logging.basicConfig(
    filename='app.log',          # Name of the log file
    filemode='a',                # Mode to open the file ('w' for overwrite, 'a' for append)
    format='%(asctime)s - %(levelname)s - %(message)s', # Log format
    level=logging.DEBUG          # Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


class FocusableContainer(Container, can_focus=True):
    """Focusable container widget."""


class MessageBox(Widget):
    def __init__(self, text: str, role: str, markdown_str: str = "") -> None:
        super().__init__()
        self.text = text
        self.markdown_str = markdown_str
        self.role = role

    def compose(self) -> ComposeResult:
        if self.markdown_str:
            with Widget(classes=f"message {self.role}"):
                yield Static(self.text)

                if self.markdown_str:
                    yield Markdown(self.markdown_str, id="markdown_box")
        else:
            yield Static(self.text, classes=f"message {self.role}")


class NeptunChatApp(App):
    TITLE = "neptun-chatbot"
    SUB_TITLE = "The NEPTUN-CHATBOT directly in your terminal"
    CSS_PATH = Path(__file__).parent / "static" / "style.css"

    def on_mount(self) -> None:
        self.conversation = Conversation()
        self.query_one("#message_input", Input).focus()
        self.call_later(self.list_existing_chats)

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q / CTRL+C"),
        ("ctrl+x", "clear", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with FocusableContainer(id="conversation_box"):
            yield MessageBox(
                "Welcome to neptun-chatbot!\n"
                "Type your question, click enter or 'send' button "
                "and wait for the response.\n"
                "At the bottom you can find few more helpful commands.",
                role="info"
            )
        with Horizontal(id="input_box"):
            yield Input(placeholder="Enter your message", id="message_input")
            yield Button(label="Send", id="send_button")
        yield Footer()

    async def on_button_pressed(self) -> None:
        await self.process_conversation()

    async def on_input_submitted(self) -> None:
        await self.process_conversation()

    def toggle_widgets(self, *widgets: Widget) -> None:
        for w in widgets:
            w.disabled = not w.disabled

    async def list_existing_chats(self):
        conversation_box = self.query_one("#conversation_box", Container)
        await self.conversation.run()

        for message in self.conversation.messages[-5:]:
            await conversation_box.mount(
                MessageBox(
                    role=message.role,
                    text=message.content
                )
            )

    async def process_conversation(self) -> None:
        message_input = self.query_one("#message_input", Input)
        button = self.query_one("#send_button", Button)
        conversation_box = self.query_one("#conversation_box", Container)

        # Disable the widgets while answering
        self.toggle_widgets(message_input, button)

        user_message = message_input.value
        user_message_box = MessageBox(role="user", text=user_message)
        await conversation_box.mount(user_message_box)

        conversation_box.scroll_end(animate=False)

        logging.debug(f"User message: {user_message}")

        with message_input.prevent(Input.Changed):
            message_input.value = ""

        try:
            result = await self.conversation.send(user_message)
            logging.debug(f"API response: {result}")

            if result:
                await conversation_box.mount(
                    MessageBox(role="assistant", text=result.content)
                )
            else:
                logging.error("No result returned from conversation.send()")
        except Exception as e:
            logging.error(f"Error in conversation: {e}")
            logging.error("Exception details:\n" + traceback.format_exc())

        self.toggle_widgets(message_input, button)
        conversation_box.scroll_end(animate=False)

    def action_clear(self) -> None:
        self.conversation.clear()
        conversation_box = self.query_one("#conversation_box", Container)

        for child in conversation_box.children:
            child.remove()


def main():
    neptun_bot = NeptunChatApp()

    neptun_bot.run()

if __name__ == "__main__":
    main()