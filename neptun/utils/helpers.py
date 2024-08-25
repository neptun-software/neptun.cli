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
    def __init__(self, message):
        self.message = message

    def extract_sections(self):
        sections = []
        in_markdown = False
        markdown_content = []
        text_content = []
        data = self.extract_message_parts()
        print(data)

        for item in data:
            if item == '```':
                if in_markdown:
                    # End of Markdown block
                    if markdown_content:
                        sections.append(
                            ResponseContent(content=self.to_markdown_code_block(''.join(markdown_content)),
                                            type="markdown"))
                        markdown_content = []
                    in_markdown = False
                else:
                    # Start of Markdown block
                    if text_content:
                        sections.append(
                            ResponseContent(content=self.to_text_block(''.join(text_content)), type="text"))

                        text_content = []
                    in_markdown = True
            elif in_markdown:
                markdown_content.append(item)
            else:
                # Collect text content
                text_content.append(item)

        if text_content:
            sections.append(ResponseContent(content=self.to_text_block(''.join(text_content)), type="text"))
        if markdown_content:
            sections.append(ResponseContent(content=self.to_markdown_code_block(''.join(markdown_content))
                                            , type="markdown"))

        return sections

    @staticmethod
    def to_markdown_code_block(code_str: str) -> str:
        return code_str.replace('\\n', '\n').replace("\\", '"')

    @staticmethod
    def to_text_block(code_str: str) -> str:
        return code_str.replace('\\n', '\n').replace("\\", '"')

    def extract_message_parts(self):
        segments = re.findall(r'0:"(.*?)"', self.message)
        return segments

    @staticmethod
    def pretty_print(message):
        wrapper = textwrap.TextWrapper(width=50)
        wrapped_text = wrapper.fill(text=message)
        return wrapped_text
