import asyncio
from neptun.utils.managers import ConfigManager

class NeptunChatBot:
    def __init__(self):
        self.config_manger = ConfigManager()

    def respond(self, message: str) -> str:
        if "hello" in message.lower():
            return "Hello! How can I help you today?"
        elif "bye" in message.lower():
            return "Goodbye! Have a nice day!"
        elif "show docs" in message.lower():
            return "markdown:## Documentation\n\n- Item 1\n- Item 2"
        else:
            return "I'm sorry, I don't understand that."
