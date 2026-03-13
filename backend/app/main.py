import logging

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
