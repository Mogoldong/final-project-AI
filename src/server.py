from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import gradio as gr
from fastapi.responses import FileResponse
from src.agent.bot import make_agent
from src.app import build_interface

load_dotenv()

app = FastAPI(
    title="AI Chef Bot API",
    description="AI Chef Bot API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 스키마
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"

class ChatResponse(BaseModel):
    message: str
    thread_id: str

agent = make_agent()

@app.get("/")
def read_root():
    return FileResponse("src/index.html")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Chef Bot API"
    }

@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    try:
        response = agent.chat(request.message, thread_id=request.thread_id)
        return ChatResponse(
            message=response,
            thread_id=request.thread_id
        )
    except Exception as e:
        return ChatResponse(
            message=f"Error: {str(e)}",
            thread_id=request.thread_id
        )

# Gradio UI mount
gradio_app = build_interface().queue()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")

if __name__ == "__main__":
    print("FastAPI server starting...")
    print("URL: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
