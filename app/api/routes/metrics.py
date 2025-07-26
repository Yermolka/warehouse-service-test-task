from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(prefix="/metrics")


@router.get("/")
async def get_consumer_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
