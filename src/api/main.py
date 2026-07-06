from __future__ import annotations

"""FastAPI application entry point."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.mock_routes import router as mock_router
from src.api.routes import router

app = FastAPI(
    title="Travel History Reconstruction API",
    description="Extract structured travel records from passport stamp images.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(mock_router)
