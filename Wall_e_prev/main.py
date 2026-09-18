from core.agent import agent_router
from utils.ollama_utils import trim


if __name__ == "__main__":
    history = []

    while True:
        user = input("you: ")
        response = agent_router(query=user, history=history)
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": response})
        history = trim(history=history)
        print("-*_" * 10)