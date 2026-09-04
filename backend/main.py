from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title=settings.APP_NAME, 
    description="AI-powered conversational weather intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "WeatherGPT is healthy"
    }

from app.api import auth

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
