from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from services.movement_service import MovementService

router = APIRouter(prefix="/movement-details", tags=["movement details"])

@router.get("/{movement_id}")
async def get_movement_details(
    movement_id: str, 
    db: AsyncSession = Depends(get_db)
):
    details = await MovementService.get_movement_details(db, movement_id)
    if not details:
        raise HTTPException(status_code=404, detail="Movement not found")
    return details