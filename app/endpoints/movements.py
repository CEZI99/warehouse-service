from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.schemas import Movement
from app.models.database import get_db
from app.services.movement_service import MovementService

router = APIRouter(prefix="/movements", tags=["movements"])

@router.get("/{movement_id}", response_model=Movement)
async def get_movement(
    movement_id: str, 
    db: AsyncSession = Depends(get_db)
):
    movement = await MovementService.get_movement(db, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return movement