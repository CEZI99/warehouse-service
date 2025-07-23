from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.endpoints import movements, warehouse_stocks, movement_details

app = FastAPI(
    title="Warehouse Movement Service",
    description="Microservice for tracking warehouse movements",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movements.router)
app.include_router(warehouse_stocks.router)
app.include_router(movement_details.router)