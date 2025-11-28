from fastapi import FastAPI
from api.routes import router
from core.config import settings

app = FastAPI(
    title="MercadoLocal-IA",
    version="1.0.0"
)

app.include_router(router, prefix=settings.API_VERSION)
