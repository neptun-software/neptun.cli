import httpx
import re
API_URL = "https://neptun-webui.vercel.app/api/ai/huggingface/google/gemma-2-27b-it/chat?chat_id=104"

# Define the message history (conversation context)
payload = {
    "messages": [
        {"role": "user", "content": "Generate me fizzbuzz in java!"},
        {"role": "assistant", "content": "fdsafdsafa"},
        {"role": "user", "content": "Explain this fizzbuzz game to me"}
    ]
}

# Define headers (including session cookie)
session_cookie = "Fe26.2**d78c6834b5666ada7b76c6c4cc8f88364774df386f48b065b89d1712e0e6e8ce*KY1Zh8aoyX9dkUlMfoiYsg*pWeBbDqdb9z6VOeHPOTzfvOKhOskWuxeF7i3lJg9anoElcHIc24n5J8auQzwPhdzrSkKPxBraB_04lFruSKmz0X5DoDnz1NiPRdalsdJA6nlNKJYdmAJAYE-REHlKLgqli-47NrUo-2v2OBd9bDxhGP8GWZKmMHEBWJ2eqEc0di8-2CoQfw-JmHi5maVoJggvRsbzJ6O7VNPuEYMxejQB2aVRSJiA3XjjeWWEVectg9F2NDUOqqy5JqAqceBQk1maDeFcUMLpBFQfkPIkHkacE8Lkaox6oNW0GuW3zKEMa_rhLihUbNpF3a8L-p8dZrHCCjn7532hxz6cwSxZSCGXn25UfWxURFC-FSjgVsZVm5qneS1qmE9S3W1qLuogyjiYPjnpGvWj4Inds-xWjhi2w**ecb51b5bd889ad1e670e09143d6c5b272e33972cb6ee18e2c1fd7723b636b772*9iHlU0L70qz2ppS5KnrmYFMS2HXHHwvlqJaOO4zM24E"
headers = {
    "Content-Type": "application/json",
}


def clean_streamed_data(chunk: str) -> str:
    """Removes unnecessary prefixes and cleans the streamed data."""
    cleaned_chunk = re.sub(r'\d+:"', '', chunk)  # Remove `0:"`, `1:"`, etc.
    cleaned_chunk = cleaned_chunk.replace('\n', ' ')  # Replace newlines with spaces
    cleaned_chunk = cleaned_chunk.strip()  # Trim leading/trailing spaces
    return cleaned_chunk


def read_mdn_webstream():
    """Streams response immediately and removes unwanted characters."""
    with httpx.Client(cookies={"neptun-session": session_cookie}) as client:
        with client.stream("POST", API_URL, json=payload, headers=headers, timeout=60) as response:
            if response.status_code == 200:
                print("🔄 Streaming response from API...\n")
                for chunk in response.iter_bytes():
                    if chunk:
                        decoded_text = chunk.decode("utf-8", errors="ignore")
                        cleaned_text = clean_streamed_data(decoded_text)
                        print(cleaned_text, end="", flush=True)  # Print in real-time
            else:
                # Try to read a small part of the error response
                error_preview = next(response.iter_bytes(chunk_size=512)).decode("utf-8", errors="ignore")
                print(f"❌ Failed to fetch stream. Status: {response.status_code}, Response: {error_preview}")


if __name__ == "__main__":
    read_mdn_webstream()