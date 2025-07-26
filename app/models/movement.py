from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID

from sqlmodel import Field, SQLModel


class MovementEvent(Enum):
    DEPARTURE = "departure"
    ARRIVAL = "arrival"
    FULL = "full"


class WarehouseProducts(SQLModel, table=True):
    __tablename__: ClassVar[str] = "warehouse_products"

    warehouse_id: UUID = Field(primary_key=True)
    product_id: UUID = Field(primary_key=True)
    quantity: int = Field(nullable=False)

    @staticmethod
    def get_cache_key(warehouse_id: UUID, product_id: UUID) -> str:
        return f"warehouse_products:{warehouse_id}:{product_id}"


@dataclass(kw_only=True)
class MovementData:
    movement_id: UUID
    warehouse_id: UUID
    timestamp: datetime
    event: MovementEvent
    product_id: UUID
    quantity: int

    @classmethod
    def from_dict(cls, data: dict) -> "MovementData":
        return cls(
            movement_id=UUID(hex=data["movement_id"]),
            warehouse_id=UUID(hex=data["warehouse_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event=MovementEvent(data["event"]),
            product_id=UUID(hex=data["product_id"]),
            quantity=data["quantity"],
        )

    def to_dict(self) -> dict:
        return {
            "movement_id": self.movement_id.hex,
            "warehouse_id": self.warehouse_id.hex,
            "timestamp": self.timestamp.isoformat(),
            "event": self.event.value,
            "product_id": self.product_id.hex,
            "quantity": self.quantity,
        }


class MovementBase(SQLModel):
    id: UUID = Field(primary_key=True)
    warehouse_id_from: UUID = Field(nullable=False, default=UUID(int=0))
    warehouse_id_to: UUID = Field(nullable=False, default=UUID(int=0))
    product_id: UUID = Field(nullable=False, default=UUID(int=0))

    @property
    def event_type(self) -> MovementEvent:
        nil_uuid = UUID(int=0)
        from_is_set = self.warehouse_id_from != nil_uuid
        to_is_set = self.warehouse_id_to != nil_uuid
        if from_is_set and to_is_set:
            return MovementEvent.FULL
        elif from_is_set:
            return MovementEvent.DEPARTURE
        else:
            return MovementEvent.ARRIVAL


class Movement(MovementBase, table=True):
    __tablename__: ClassVar[str] = "movements"

    departure_at: datetime = Field(nullable=False, default=datetime.min)
    arrival_at: datetime = Field(nullable=False, default=datetime.min)
    quantity_from: int = Field(nullable=False, default=0)
    quantity_to: int = Field(nullable=False, default=0)

    @classmethod
    def from_data(cls, data: MovementData) -> "Movement":
        movement = cls(id=data.movement_id, product_id=data.product_id)
        movement.merge_data_values(data)
        return movement

    def merge_data_values(self, data: MovementData):
        if data.event == MovementEvent.DEPARTURE:
            self.warehouse_id_from = data.warehouse_id
            self.departure_at = data.timestamp
            self.quantity_from = data.quantity
        else:
            self.warehouse_id_to = data.warehouse_id
            self.arrival_at = data.timestamp
            self.quantity_to = data.quantity

    @staticmethod
    def get_cache_key(movement_id: UUID) -> str:
        return f"movement:{movement_id}"


class MovementPublic(MovementBase):
    time_diff: float
    quantity_diff: int

    @classmethod
    def from_movement(cls, movement: Movement) -> "MovementPublic":
        time_diff = 0
        if movement.arrival_at != datetime.min and movement.departure_at != datetime.min:
            time_diff = (movement.arrival_at - movement.departure_at).total_seconds()

        quantity_diff = movement.quantity_from - movement.quantity_to
        return cls(
            id=movement.id,
            warehouse_id_from=movement.warehouse_id_from,
            warehouse_id_to=movement.warehouse_id_to,
            product_id=movement.product_id,
            time_diff=time_diff,
            quantity_diff=quantity_diff,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "MovementPublic":
        return cls(
            id=UUID(hex=data["id"]),
            warehouse_id_from=UUID(hex=data["warehouse_id_from"]),
            warehouse_id_to=UUID(hex=data["warehouse_id_to"]),
            product_id=UUID(hex=data["product_id"]),
            time_diff=data["time_diff"],
            quantity_diff=data["quantity_diff"],
        )
