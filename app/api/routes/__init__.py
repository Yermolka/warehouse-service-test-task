from .health import router as health_router
from .metrics import router as metrics_router
from .movements import router as movements_router
from .warehouses import router as warehouses_router

__all__ = ["health_router", "metrics_router", "movements_router", "warehouses_router"]
