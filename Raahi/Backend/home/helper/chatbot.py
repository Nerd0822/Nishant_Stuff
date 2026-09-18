import ollama
import os

# Use host.docker.internal to reach host machine from inside Docker
# Falls back to localhost for local development
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
client = ollama.Client(host=OLLAMA_URL)


def generate(prompt: str) -> str:
    response = client.chat(
        model="qwen3:1.7b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response["message"]["content"]


if __name__ == "__main__":
    while True:
        user = input("you: ")

        if user.lower() in ["quit", "bye", "exit"]:
            break

        print(f"Raahi: {generate(str(user))}")
