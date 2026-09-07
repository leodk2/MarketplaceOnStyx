from dataclasses import dataclass
from datetime import datetime

from Entities.Order import OrderStatus


@dataclass
class OrderHistory:
    orderId: int
    createdAt: datetime
    status: OrderStatus
