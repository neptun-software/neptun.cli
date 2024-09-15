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
