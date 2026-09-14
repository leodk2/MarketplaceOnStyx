from dataclasses import dataclass
from datetime import datetime

from Entities.Packages import PackageStatus


@dataclass(frozen=True)
class DeliveryNotification:
    order_id: int
    customer_id: int
    package_id: int
    seller_id: int
    product_id: int
    product_name: str
    package_status: PackageStatus
    delivery_date: datetime