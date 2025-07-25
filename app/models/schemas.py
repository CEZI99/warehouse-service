from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class KafkaEvent(BaseModel):
    id: str
    source: str
    specversion: str
    type: str
    datacontenttype: str
    dataschema: str
    time: int
    subject: str
    destination: str
    data: 'EventData'

class EventData(BaseModel):
    movement_id: str
    warehouse_id: str
    timestamp: str
    event: str
    product_id: str
    quantity: int

class Movement(BaseModel):
    id: str
    movement_type: str
    warehouse_id: str
    product_id: str
    quantity: int
    timestamp: datetime
    related_movement_id: Optional[str] = None

    class Config:
        orm_mode = True

class WarehouseStock(BaseModel):
    warehouse_id: str
    product_id: str
    quantity: int
    last_updated: datetime

    class Config:
        orm_mode = True

KafkaEvent.model_rebuild()
