import logging

from fastapi import FastAPI

from backend.app.api.routes import router as sentiment_router
from backend.app.config import settings

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

logger.info(f"Initializing {settings.app_name} in {settings.app_env} environment")


@app.get("/health", tags=["Health"])
def health_check():
    """Service health check endpoint."""
    return {"status": "ok", "environment": settings.app_env}


app.include_router(sentiment_router)
