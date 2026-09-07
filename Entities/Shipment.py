from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ShipmentStatus(Enum):
    APPROVED = 0
    CONCLUDED = 1
    DELIVERY_IN_PROGRESS = 2


@dataclass
class Shipment:
    shipment_id: int
    order_id: int
    customer_id: int
    package_count: int
    total_freight: float
    first_name: str
    last_name: str
    street: str
    zip_code: str
    status: ShipmentStatus
    city: str
    state: str
    request_date: datetime
