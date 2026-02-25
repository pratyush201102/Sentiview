from fastapi import FastAPI

from backend.app.api.routes import router as sentiment_router
from backend.app.config import settings


app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.app_env}


app.include_router(sentiment_router)
