from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.scroll_view import ScrollView
from textual.widgets import Footer, Header, Placeholder, Input, Button
from pathlib import Path
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Button, Static
from textual.containers import Horizontal, Container
from neptun.bot.chat import Conversation

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
        self.conversation.run()
        self.query_one("#message_input", Input).focus()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="conversation_box")
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

        conversation_box.mount(
            MessageBox(
                "Answer",
                "answer",
            )
        )

        self.toggle_widgets(message_input, button)
        conversation_box.scroll_end(animate=False)


if __name__ == "__main__":
    app = NeptunChatApp()
    app.run()
