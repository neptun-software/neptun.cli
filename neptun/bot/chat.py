import asyncio

from neptun.model.http_requests import ChatRequest, Message
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from rich.console import Console
from rich.markdown import Markdown
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatMessage, ChatMessagesHttpResponse, ErrorResponse
from neptun.utils.helpers import ChatResponseConverter

class Conversation:
    def __init__(self):
        self.chat_service = ChatService()
        self.messages: list[ChatMessage] = []
        self.console = Console()

    def fetch_latest_messages(self):
        response = self.chat_service.get_chat_messages_by_chat_id()

        if isinstance(response, ChatMessagesHttpResponse):
            self.messages = response.chat_messages
            print(response.chat_messages)
        else:
            self.console.print(f"Error fetching messages: {response.detail}", style="bold red")

    async def send(self, message: str):

        messages = []

        for iterator in self.messages:
            messages.append(Message(
                role=iterator.actor,
                content=iterator.message
            ))

        messages.append(Message(
            role="user",
            content=message
        ))

        chat_request = ChatRequest(messages=messages)

        result = self.chat_service.post_chat_message(
            messages=chat_request
        )

        return result

    def response(self, choice: str) -> None:
        self.messages.append({"role": "assistant", "content": choice})

    def clear(self) -> None:
        self.messages = []

    def run(self):
        self.fetch_latest_messages()


if __name__ == "__main__":
    conversation = Conversation()
    conversation.run()
