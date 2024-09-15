import asyncio
from neptun.model.http_requests import ChatRequest, Message
from neptun.utils.managers import ConfigManager
from neptun.utils.services import ChatService
from rich.console import Console
from rich.markdown import Markdown
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatMessage, ChatMessagesHttpResponse, ErrorResponse
from neptun.utils.helpers import ChatResponseConverter

import logging

logging.basicConfig(
    filename='app.log',  # Name of the log file
    filemode='a',  # Mode to open the file ('w' for overwrite, 'a' for append)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    level=logging.DEBUG  # Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


class Conversation:
    def __init__(self):
        self.chat_service = ChatService()
        self.messages: list[Message] = []
        self.console = Console()
        self.chat_response_converter = ChatResponseConverter()

    async def fetch_latest_messages(self):
        response = await self.chat_service.get_chat_messages_by_chat_id()

        if isinstance(response, ChatMessagesHttpResponse):
            logging.debug(f"Messages Loaded: {response.chat_messages}")
            self.messages = [Message(role=msg.actor, content=msg.message) for msg in response.chat_messages]
        else:
            self.console.print(f"Error fetching messages: {response.detail}", style="bold red")

    def parse_response(self, response: str) -> str:
        lines = response.splitlines()

        parsed_lines = []

        for line in lines:
            parsed_line = line.split(':')[1].strip().strip('"')
            parsed_lines.append(parsed_line)

        return ''.join(parsed_lines)

    async def send(self, message: str) -> Message | None:
        self.messages.append(Message(role="user", content=message))

        chat_request = ChatRequest(messages=self.messages)

        logging.debug(f"Sending chat request: {chat_request.model_dump()}")

        try:
            response = await self.chat_service.post_chat_message(chat_request)

            converted_message = self.chat_response_converter.parse_response(response)

            logging.debug(f"Received response: {converted_message}")

            self.messages.append(Message(role="assistant", content=converted_message))

            return self.messages[-1]
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return None

    def clear(self) -> None:
        self.messages = []

    async def run(self):
        await self.fetch_latest_messages()


async def main():
    conversation = Conversation()

    result = await conversation.send("Hello world!")

    print(result.message)


if __name__ == "__main__":
    asyncio.run(main())
