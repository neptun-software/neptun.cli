import asyncio
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from rich.console import Console
from rich.markdown import Markdown
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatMessage, ChatMessagesHttpResponse, ErrorResponse


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
            print("dsfsafds")
            self.console.print(f"Error fetching messages: {response.detail}", style="bold red")

    def send(self, message: str) -> list[str]:
        self.messages.append({"role": "user", "content": message})

        response = f"Echo: {message}"
        self.messages.append({"role": "assistant", "content": response})

        return [response]

    def response(self, choice: str) -> None:
        self.messages.append({"role": "assistant", "content": choice})

    def clear(self) -> None:
        self.messages = []

    def run(self):
        self.fetch_latest_messages()

        while True:
            msg = input("Type your message: ")
            response = self.send(msg)
            print("Here is your message: ", self.messages[-1])


if __name__ == "__main__":
    conversation = Conversation()
    conversation.run()
