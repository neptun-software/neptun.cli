import httpx
import re
from rich.console import Console
from rich.markdown import Markdown
import mdformat


API_URL = "https://neptun-webui.vercel.app/api/ai/huggingface/google/gemma-2-27b-it/chat?chat_id=104&is_playground=false"

payload = {
    "messages": [
        {"role": "user", "content": "Generate me fizzbuzz in java!"},
        {"role": "assistant", "content": "fdsafdsafa"},
        {"role": "user", "content": "Explain this fizzbuzz game to me"},
        {"role": "user", "content": "Implement it in java and print it to the console"},

    ]
}

session_cookie = "Fe26.2**d78c6834b5666ada7b76c6c4cc8f88364774df386f48b065b89d1712e0e6e8ce*KY1Zh8aoyX9dkUlMfoiYsg*pWeBbDqdb9z6VOeHPOTzfvOKhOskWuxeF7i3lJg9anoElcHIc24n5J8auQzwPhdzrSkKPxBraB_04lFruSKmz0X5DoDnz1NiPRdalsdJA6nlNKJYdmAJAYE-REHlKLgqli-47NrUo-2v2OBd9bDxhGP8GWZKmMHEBWJ2eqEc0di8-2CoQfw-JmHi5maVoJggvRsbzJ6O7VNPuEYMxejQB2aVRSJiA3XjjeWWEVectg9F2NDUOqqy5JqAqceBQk1maDeFcUMLpBFQfkPIkHkacE8Lkaox6oNW0GuW3zKEMa_rhLihUbNpF3a8L-p8dZrHCCjn7532hxz6cwSxZSCGXn25UfWxURFC-FSjgVsZVm5qneS1qmE9S3W1qLuogyjiYPjnpGvWj4Inds-xWjhi2w**ecb51b5bd889ad1e670e09143d6c5b272e33972cb6ee18e2c1fd7723b636b772*9iHlU0L70qz2ppS5KnrmYFMS2HXHHwvlqJaOO4zM24E"
headers = {
    "Content-Type": "application/json",
}
console = Console()


def clean_text(line):
    """Removes the leading 0:" and trailing quotes."""
    match = re.match(r'0:"(.*)"', line)
    return match.group(1) if match else line


def read_mdn_webstream():
    with httpx.Client(cookies={"neptun-session": session_cookie}) as client:
        with client.stream("POST", API_URL, json=payload, headers=headers, timeout=60) as response:
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
                            cleaned_text = clean_text(line.strip())  # Strip extra whitespace
                            print(cleaned_text, end="", flush=True)

                if buffer:
                    print(clean_text(buffer.strip()), end="", flush=True)

            else:
                error_preview = next(response.iter_bytes(chunk_size=512)).decode("utf-8", errors="ignore")
                print(f"❌ Failed to fetch stream. Status: {response.status_code}, Response: {error_preview}")


if __name__ == "__main__":
    read_mdn_webstream()
