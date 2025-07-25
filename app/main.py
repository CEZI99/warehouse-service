from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.endpoints import warehouses
from app.dependencies import init_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cache()
    yield

app = FastAPI(
    title="Warehouse Movement Service",
    description="Microservice for tracking warehouse movements",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(warehouses.router)
