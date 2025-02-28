import asyncio
import traceback
from textual.await_complete import AwaitComplete
from rich.progress import Progress, SpinnerColumn, TextColumn
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import Horizontal, Container
from textual.widgets import Footer, Header, Input, Button, Static
from textual.widget import Widget
from textual.widgets import Markdown
from pathlib import Path
from rich.progress import Progress, BarColumn
from neptun.bot.chat import Conversation
import logging
from textual.widgets import LoadingIndicator
from rich.spinner import Spinner

from rich.progress import Progress, BarColumn

from textual.app import App, ComposeResult
from textual.widgets import Static

from neptun.model.http_requests import Message, ChatRequest
from neptun.utils.helpers import ChatResponseConverter
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService

logging.basicConfig(
    filename='app.log',          # Name of the log file
    filemode='a',                # Mode to open the file ('w' for overwrite, 'a' for append)
    format='%(asctime)s - %(levelname)s - %(message)s', # Log format
    level=logging.DEBUG          # Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


class FocusableContainer(Container, can_focus=True):
    """Focusable container widget."""


class SpinnerWidget(Static):
    def __init__(self):
        super().__init__("")
        self._spinner = Spinner("moon")

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 60, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(self._spinner)


class MessageBox(Widget):
    text = reactive("", recompose=True)
    markdown = reactive("", recompose=True)

    def __init__(self, text: str, role: str, markdown_str: str = "") -> None:
        super().__init__()
        self.text = text
        self.markdown_str = markdown_str
        self.role = role
        self.text_box = None  # ✅ Store reference to avoid query issues

    def compose(self) -> ComposeResult:
        if self.markdown_str:
            with Widget(classes=f"message {self.role}"):
                self.text_box = Static(self.text, id="text_box")  # ✅ Save reference
                yield Static(self.text, id="text_box")

                if self.markdown_str:
                    yield Markdown(self.markdown_str, id="markdown_box")
        else:
            yield Static(self.text, classes=f"message {self.role}")

    def watch_text(self, old_value: str, new_value: str):
        if self.text_box:
            self.text_box.update(new_value)

    def watch_markdown_str(self, old_value: str, new_value: str):
        if new_value:
            self.query_one("#markdown_box", Markdown).update(new_value)

    async def update_text(self, new_text: str) -> None:
        self.text = new_text
        self.refresh()


class IndeterminateProgress(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.progress = Progress()
        self.task_id = self.progress.add_task("Loading...", total=None)
        self.loading_indicator = LoadingIndicator()

    def compose(self) -> ComposeResult:
        yield self.loading_indicator

    def on_mount(self) -> None:
        self.update_render = self.set_interval(
            1 / 60, self.update_progress_bar
        )

    def update_progress_bar(self) -> None:
        self.update(self.progress)


class NeptunChatApp(App):
    TITLE = "neptun-chatbot"
    SUB_TITLE = "The NEPTUN-CHATBOT directly in your terminal"
    CSS_PATH = Path(__file__).parent / "static" / "style.css"

    def on_mount(self) -> None:
        self.chat_response_converter = ChatResponseConverter()
        self.messages: list[Message] = []
        self.chat_service = ChatService()
        config_manager = ConfigManager()
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

    async def on_unmount(self) -> None:
        await self.chat_service.async_client.aclose()

    async def process_conversation(self) -> None:
        message_input = self.query_one("#message_input", Input)
        button = self.query_one("#send_button", Button)
        conversation_box = self.query_one("#conversation_box", Container)

        # Disable the widgets while answering
        self.toggle_widgets(message_input, button)

        user_message = message_input.value
        user_message_box = MessageBox(role="user", text=user_message)

        await conversation_box.mount(user_message_box)

        conversation_box.scroll_end(animate=True)

        logging.debug(f"User message: {user_message}")
        self.messages.append(Message(role="user", content=user_message))

        with message_input.prevent(Input.Changed):
            message_input.value = ""

        try:
            chat_request = ChatRequest(messages=self.messages)
            headers = {
                "Content-Type": "application/json",
            }
            chat_id = self.chat_service.config_manager.read_config("active_chat", "chat_id")
            model = self.chat_service.config_manager.read_config("active_chat", "model")
            model_publisher, model_name = self.chat_service.extract_parts(model)

            url = f"{self.chat_service.config_manager.read_config('utils', 'neptun_api_server_host')}/ai/huggingface/{model_publisher}/{model_name}/chat?chat_id={chat_id}"
            full_response = ""
            client = self.chat_service.async_client
            async with client.stream(
                    "POST",
                    url,
                    json=chat_request.model_dump(),
                    headers=headers,
                    timeout=60
            ) as response:
                if response.status_code == 200:
                    buffer = ""
                    assistant_message_box = MessageBox("", "assistant")
                    await conversation_box.mount(assistant_message_box)
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            decoded_text = chunk.decode("utf-8", errors="ignore")
                            buffer += decoded_text
                            conversation_box.scroll_end(animate=True)

                            lines = buffer.split("\n")
                            buffer = lines.pop()

                            for line in lines:
                                cleaned_text = self.chat_response_converter.clean_line(line.strip())
                                """
                                await conversation_box.mount(
                                    MessageBox(full_response, "assistant")
                                )
                                """
                                full_response += cleaned_text
                                #await assistant_message_box.update_text(cleaned_text)
                                conversation_box.scroll_end(animate=True)
                    if buffer:
                        cleaned_text = self.chat_response_converter.clean_line(buffer.strip())
                        full_response += cleaned_text
                else:
                    # Handle non-200 responses
                    error_content = await response.aread()
                    await conversation_box.mount(
                        MessageBox(f"API Error: {response.status_code}\n{error_content}", "error")
                    )

        except Exception as e:
            logging.error(f"Error in conversation: {e}")
            logging.error("Exception details:\n" + traceback.format_exc())

        self.toggle_widgets(message_input, button)
        conversation_box.scroll_end(animate=True)

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