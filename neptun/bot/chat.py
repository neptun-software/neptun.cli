import asyncio
import re

from neptun.model.http_requests import ChatRequest, Message
from rich.console import Console
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatMessage, ChatMessagesHttpResponse, ErrorResponse
from neptun.utils.helpers import ChatResponseConverter
import httpx
import logging

# implement chatgpt chat only

logging.basicConfig(
    filename='app.log',  # Name of the log file
    filemode='a',  # Mode to open the file ('w' for overwrite, 'a' for append)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    level=logging.DEBUG
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

    def clean_text(self, line):
        match = re.match(r'0:"(.*)"', line)
        return match.group(1) if match else line

    async def ask(self, message):
        self.messages.append(Message(role="user", content=message))

        chat_request = ChatRequest(messages=self.messages)
        headers = {
            "Content-Type": "application/json",
        }
        session_cookie = "Fe26.2**d78c6834b5666ada7b76c6c4cc8f88364774df386f48b065b89d1712e0e6e8ce*KY1Zh8aoyX9dkUlMfoiYsg*pWeBbDqdb9z6VOeHPOTzfvOKhOskWuxeF7i3lJg9anoElcHIc24n5J8auQzwPhdzrSkKPxBraB_04lFruSKmz0X5DoDnz1NiPRdalsdJA6nlNKJYdmAJAYE-REHlKLgqli-47NrUo-2v2OBd9bDxhGP8GWZKmMHEBWJ2eqEc0di8-2CoQfw-JmHi5maVoJggvRsbzJ6O7VNPuEYMxejQB2aVRSJiA3XjjeWWEVectg9F2NDUOqqy5JqAqceBQk1maDeFcUMLpBFQfkPIkHkacE8Lkaox6oNW0GuW3zKEMa_rhLihUbNpF3a8L-p8dZrHCCjn7532hxz6cwSxZSCGXn25UfWxURFC-FSjgVsZVm5qneS1qmE9S3W1qLuogyjiYPjnpGvWj4Inds-xWjhi2w**ecb51b5bd889ad1e670e09143d6c5b272e33972cb6ee18e2c1fd7723b636b772*9iHlU0L70qz2ppS5KnrmYFMS2HXHHwvlqJaOO4zM24E"
        API_URL = "https://neptun-webui.vercel.app/api/ai/huggingface/google/gemma-2-27b-it/chat?chat_id=104"
        with httpx.Client(cookies={"neptun-session": session_cookie}) as client:
            with client.stream("POST", API_URL, json=chat_request.model_dump(), headers=headers, timeout=60) as response:
                if response.status_code == 200:
                    print("🔄 Streaming response from API...\n")
                    buffer = ""

                    for chunk in response.iter_bytes():
                        if chunk:
                            decoded_text = chunk.decode("utf-8", errors="ignore")
                            buffer += decoded_text  # Append chunk to buffer

                            lines = buffer.split("\n")
                            buffer = lines.pop()

                            for line in lines:
                                cleaned_text = self.clean_text(line.strip())  # Strip extra whitespace
                                print(cleaned_text, end="", flush=True)

                    if buffer:
                        print(self.clean_text(buffer.strip()), end="", flush=True)

                else:
                    error_preview = next(response.iter_bytes(chunk_size=512)).decode("utf-8", errors="ignore")
                    print(f"❌ Failed to fetch stream. Status: {response.status_code}, Response: {error_preview}")

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
