import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.routes import router as sentiment_router
from backend.app.config import settings
from backend.app.db.session import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Real-time sentiment analysis API for Reddit posts",
    version="1.0.0"
)

# Configure CORS with restricted origins (security best practice)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

logger.info(f"Initializing {settings.app_name} in {settings.app_env} environment")


@app.get("/health", tags=["Health"])
def health_check():
    """Service health check endpoint."""
    database_status = "up"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database_status = "down"

    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": database_status,
    }


app.include_router(sentiment_router)
