from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, chat

app = FastAPI(
    title="Migravio AI Service",
    description="AI-powered immigration assistant API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://migravio.ai",
        "https://www.migravio.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/chat", tags=["chat"])
