from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, async_session_maker
from app.core.redis import redis_client
from app.racing.seed_data import seed_verified_2024_data
from app.api.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed baseline data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        await seed_verified_2024_data(session)

    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.close()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="APEX GP — Formula 1 Racing, Intelligence and Championship Platform Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "apex-gp-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
