from rich.progress import Progress, SpinnerColumn, TextColumn
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.scroll_view import ScrollView
from textual.widgets import Footer, Header, Placeholder, Input, Button
from pathlib import Path
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Button, Static
from textual.containers import Horizontal, Container
from neptun.bot.chat import Conversation


class FocusableContainer(Container, can_focus=True):
    """Focusable container widget."""


class MessageBox(Widget):
    def __init__(self, text: str, role: str) -> None:
        self.text = text
        self.role = role
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(self.text, classes=f"message {self.role}")


class NeptunChatApp(App):
    TITLE = "neptun-chatbot"
    SUB_TITLE = "The NEPTUN-CHATBOT directly in your terminal"
    CSS_PATH = Path(__file__).parent / "static" / "style.css"

    def on_mount(self) -> None:
        self.conversation = Conversation()
        self.query_one("#message_input", Input).focus()
        self.list_existing_chats()

    BINDINGS = [  # 🆕
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

    def list_existing_chats(self):
        conversation_box = self.query_one("#conversation_box", Container)

        self.conversation.run()

        for message in self.conversation.messages[-5:]:
            conversation_box.mount(
                MessageBox(
                    role=message.actor,
                    text=message.message,
                )
            )

    async def process_conversation(self) -> None:
        message_input = self.query_one("#message_input", Input)
        button = self.query_one("#send_button", Button)
        conversation_box = self.query_one("#conversation_box", Container)

        if message_input.value == "":
            return

        self.toggle_widgets(message_input, button)

        message_box = MessageBox(role="question", text=message_input.value)
        conversation_box.mount(message_box)
        conversation_box.scroll_end(animate=False)

        with message_input.prevent(Input.Changed):
            message_input.value = ""


        self.toggle_widgets(message_input, button)
        conversation_box.scroll_end(animate=False)

    def action_clear(self) -> None:  # 🆕
        self.conversation.clear()
        conversation_box = self.query_one("#conversation_box")
        conversation_box.remove()
        self.mount(FocusableContainer(id="conversation_box"))


if __name__ == "__main__":
    app = NeptunChatApp()
    app.run()
