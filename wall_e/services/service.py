from fastapi import FastAPI
from pydantic import BaseModel
from agent import Agent


class ChatRequest(BaseModel):
    user: str


ai = Agent()
app = FastAPI()


@app.get("/status")
async def get_status():
    return {"output": "wall-e is live"}


@app.post("/chat")
async def chat(data: ChatRequest):
    response = ai.start(data)
    if response is None:
        return {"output": "NONE OUTPUT"}
    return {"output": ai.stream_response(response)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="service:app", reload=True, host="0.0.0.0", port=8080)
