import asyncio


class NeptunChatBot:
    def respond(self, message: str) -> str:
        # Simple bot logic for demonstration
        if "hello" in message.lower():
            return "Hello! How can I help you today?"
        elif "bye" in message.lower():
            return "Goodbye! Have a nice day!"
        else:
            return "I'm sorry, I don't understand that."
