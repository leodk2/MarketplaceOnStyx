from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PackageStatus(Enum):
    CREATED = 0
    READY_TO_SHIP = 1
    CANCELED = 2
    LOST = 3
    STOLEN = 4
    SEIZED_FOR_INSPECTION = 5
    RETURNING_TO_SENDER = 6
    RETURNED_TO_SENDER = 7
    AWAITING_PICKUP_BY_RECIEVER = 8
    SHIPPED = 9
    DELIVERED = 10


@dataclass
class Package:
    package_id: int
    order_id: int
    shipment_id: int
    seller_id: int
    product_id: int
    freight_value: float
    quantity: int
    product_name: str
    package_status: PackageStatus
    shipping_date: datetime
    delivered_time: datetime | None = None
