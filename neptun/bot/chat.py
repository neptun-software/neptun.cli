import asyncio
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from rich.console import Console
from rich.markdown import Markdown


class Conversation:
    def __init__(self):
        self.messages: list[dict] = []
        self.console = Console()

    def send(self, message: str) -> list[str]:
        self.messages.append({"role": "user", "content": message})

        response = f"Echo: {message}"
        self.messages.append({"role": "assistant", "content": response})

        return [response]

    def response(self, choice: str) -> None:
        self.messages.append({"role": "assistant", "content": choice})

    def clear(self) -> None:
        self.messages = []


if __name__ == "__main__":
    conversation = Conversation()

    while True:
        msg = input("Type your message: ")
        response = conversation.send(msg)
        print("here is your message: ", conversation.messages[-1])



