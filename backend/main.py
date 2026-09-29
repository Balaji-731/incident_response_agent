from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from backend.database.db import init_db
from backend.api import incidents, memories

load_dotenv()

# Initialize SQLite database
init_db()

app = FastAPI(
    title="Incident Response Agent API",
    description="AI-powered copilot with persistent organizational memory via Hindsight",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(memories.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": "Incident Response Agent"}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "hindsight_configured": bool(os.getenv("HINDSIGHT_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), reload=True)