from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from backend.api import incidents
load_dotenv()

app = FastAPI(
    title="Incident Response Agent API",
    description="AI-powered copilot with persistent organizational memory via Hindsight",
    version="0.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Incident Response Agent",
        "version": "0.1.0"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "hindsight_configured": bool(os.getenv("HINDSIGHT_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY"))
    }

# Include the incidents API router
app.include_router(incidents.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True)
