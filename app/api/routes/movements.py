from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from models.movement import MovementPublic
from services.warehouse import WarehouseService

router = APIRouter(prefix="/movements")


@router.get("/{movement_id}", response_model=MovementPublic)
async def get_movement(movement_id: str, warehouse_service: WarehouseService = Depends(WarehouseService)):
    try:
        movement_id_uuid = UUID(movement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid movement ID")

    movement = await warehouse_service.get_movement(movement_id_uuid)

    if movement is None:
        raise HTTPException(status_code=404, detail="Movement not found")

    return MovementPublic.from_movement(movement).model_dump(mode="json")
