from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockItem:
    product_id: int
    seller_id: int
    qty_available: int
    qty_reserved: int
    order_count: int
    ytd: int
    data: str
    version: str
    updated_at: datetime
    created_at: datetime
