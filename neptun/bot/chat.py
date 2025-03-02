import asyncio
from neptun.model.http_requests import ChatRequest, Message
from rich.console import Console
from neptun.utils.services import ChatService
from neptun.model.http_responses import ChatMessage, ChatMessagesHttpResponse
from neptun.utils.helpers import ChatResponseConverter
import logging
from rich.markdown import Markdown
from rich.live import Live

logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
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

    async def ask(self, message):
        await self.fetch_latest_messages()
        self.messages.append(Message(role="user", content=message))

        chat_request = ChatRequest(messages=self.messages)
        headers = {
            "Content-Type": "application/json",
        }
        chat_id = self.chat_service.config_manager.read_config("active_chat", "chat_id")
        model = self.chat_service.config_manager.read_config("active_chat", "model")
        model_publisher, model_name = self.chat_service.extract_parts(model)

        base_url = self.chat_service.config_manager.read_config("utils", "neptun_api_server_host")

        match model_publisher:
            case "openrouter":
                url = f"{base_url}/ai/openrouter/{model_name}/chat?chat_id={chat_id}&is_playground=false"
            case "ollama":
                url = f"{base_url}/ai/ollama/{model_name}/chat?chat_id={chat_id}&is_playground=false"
            case "cloudflare":
                url = f"{base_url}/ai/cloudflare/{model_name}/chat?chat_id={chat_id}&is_playground=false"
            case _:
                url = f"{base_url}/ai/huggingface/{model_publisher}/{model_name}/chat?chat_id={chat_id}&is_playground=false"

        full_response = ""

        with self.chat_service.client as client:
            with client.stream("POST", url, json=chat_request.model_dump(), headers=headers,
                               timeout=60) as response:
                if response.status_code == 200:
                    with Live("Streaming response from API...\n", console=self.console, refresh_per_second=10,
                              transient=True) as live:
                        buffer = ""
                        for chunk in response.iter_bytes():
                            if chunk:
                                decoded_text = chunk.decode("utf-8", errors="ignore")
                                buffer += decoded_text

                                lines = buffer.split("\n")
                                buffer = lines.pop()  # Incomplete line

                                for line in lines:
                                    cleaned_text = self.chat_response_converter.clean_line(line.strip())
                                    full_response += cleaned_text
                                    live.update(full_response)

                        if buffer:
                            cleaned_text = self.chat_response_converter.clean_line(buffer.strip())
                            full_response += cleaned_text
                            live.update(full_response)

                    # When the Live block exits, the streaming text is automatically cleared
                    md = Markdown(full_response.encode('utf-8').decode('unicode_escape'))
                    self.console.print(md)
                else:
                    error_preview = next(response.iter_bytes(chunk_size=512)).decode("utf-8", errors="ignore")
                    self.console.print(
                        f"Failed to fetch stream. Status: {response.status_code}, Response: {error_preview}")

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

