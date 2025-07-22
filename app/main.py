"""main.py"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from models import Movement, WarehouseStock
from database import SessionLocal, DBMovement, DBWarehouseStock
import uuid

app = FastAPI(
    title="Warehouse Movement Service",
    description="Microservice for tracking warehouse movements",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/movements/{movement_id}", response_model=Movement)
def get_movement(movement_id: str, db: Session = Depends(get_db)):
    db_movement = db.query(DBMovement).filter(DBMovement.id == movement_id).first()
    if not db_movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return db_movement

@app.get("/warehouses/{warehouse_id}/products/{product_id}", response_model=WarehouseStock)
def get_warehouse_stock(warehouse_id: str, product_id: str, db: Session = Depends(get_db)):
    stock = db.query(DBWarehouseStock).filter(
        DBWarehouseStock.warehouse_id == warehouse_id,
        DBWarehouseStock.product_id == product_id
    ).first()
    
    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"No stock found for product {product_id} in warehouse {warehouse_id}"
        )
    return stock

@app.get("/movements/{movement_id}/details")
def get_movement_details(movement_id: str, db: Session = Depends(get_db)):
    movement = db.query(DBMovement).filter(DBMovement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    
    details = {
        "movement_id": movement.id,
        "type": movement.movement_type,
        "warehouse": movement.warehouse_id,
        "product": movement.product_id,
        "quantity": movement.quantity,
        "timestamp": movement.timestamp
    }
    
    if movement.related_movement_id:
        related_movement = db.query(DBMovement).filter(
            DBMovement.id == movement.related_movement_id
        ).first()
        
        if related_movement:
            time_difference = abs((movement.timestamp - related_movement.timestamp).total_seconds())
            quantity_difference = abs(movement.quantity - related_movement.quantity)
            
            details.update({
                "related_movement": related_movement.id,
                "time_difference_seconds": time_difference,
                "quantity_difference": quantity_difference
            })
    
    return details

@app.get("/warehouses/{warehouse_id}/movements", response_model=List[Movement])
def get_warehouse_movements(warehouse_id: str, db: Session = Depends(get_db)):
    movements = db.query(DBMovement).filter(
        DBMovement.warehouse_id == warehouse_id
    ).order_by(DBMovement.timestamp.desc()).all()
    return movements