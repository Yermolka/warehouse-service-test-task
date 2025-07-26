from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.warehouse import WarehouseService

router = APIRouter(prefix="/warehouses")


class WarehouseProductResponse(BaseModel):
    quantity: int


@router.get("/{warehouse_id}/products/{product_id}", response_model=WarehouseProductResponse)
async def get_warehouse_product(
    warehouse_id: str, product_id: str, warehouse_service: WarehouseService = Depends(WarehouseService)
):
    try:
        warehouse_id_uuid = UUID(warehouse_id)
        product_id_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid warehouse or product ID")

    wh_product_quant = await warehouse_service.get_warehouse_product_quantity(warehouse_id_uuid, product_id_uuid)

    return {"quantity": wh_product_quant}
