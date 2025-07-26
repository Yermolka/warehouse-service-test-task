from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from api.routes import health_router, metrics_router, movements_router, warehouses_router

app = FastAPI(title="Warehouse API", version="0.0.1")


app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(movements_router, prefix="/api")
app.include_router(warehouses_router, prefix="/api")


Instrumentator().instrument(app, metric_namespace="warehouse")
