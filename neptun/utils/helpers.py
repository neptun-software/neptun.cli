import re
import textwrap
from functools import wraps
from typing import List

from pydantic import BaseModel


class ResponseContent(BaseModel):
    content: str
    type: str


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class ChatResponseConverter:
    @staticmethod
    def parse_response(response: str) -> str:
        lines = response.splitlines()

        parsed_lines = []

        for line in lines:
            parsed_line = line.split(':')[1].strip().strip('"')
            parsed_lines.append(parsed_line)

        return ''.join(parsed_lines)

    @staticmethod
    def clean_text(response: str) -> str:
        lines = text.splitlines()

        cleaned_lines = []

        for line in lines:
            if line.startswith('0:'):
                cleaned_line = line[2:]
            else:
                cleaned_line = line

            cleaned_lines.append(cleaned_line)

        formatted_text = '\n'.join(cleaned_lines)

        return formatted_text

    @staticmethod
    def clean_line(line):
        match = re.match(r'0:"(.*)"', line)
        return match.group(1) if match else line


# Example usage
text = [
    '"0: hello world"'
]


if __name__ == '__main__':
    converter = ChatResponseConverter()
    formatted_response = converter.clean_chunk("\"0: hello world\"")
    print(formatted_response)
