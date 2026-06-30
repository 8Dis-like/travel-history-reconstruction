from __future__ import annotations

"""FastAPI application entry point."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(
    title="Travel History Reconstruction API",
    description="Extract structured travel records from passport stamp images.",
    version="0.1.0",
)

app.include_router(router)
