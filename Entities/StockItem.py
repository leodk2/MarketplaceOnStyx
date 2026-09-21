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
    updated_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self):
        self.updated_at = datetime.now()
        self.created_at = datetime.now()

    def reserve(self, qty: int):
        self.qty_reserved += qty

    def confirm_reservation(self, qty):
        self.qty_reserved -= qty
        self.qty_available -= qty

    def cancel_reservation(self, qty):
        self.qty_reserved -= qty
