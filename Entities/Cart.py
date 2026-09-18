from dataclasses import dataclass

from Entities.CartItem import CartItem
from Entities.CartStatus import CartStatus
from Entities.ProductStatus import ProductStatus


@dataclass
class Cart:
    customerId: int
    status: CartStatus
    items: list[CartItem]
    instanceId: int
    divergencies: list[ProductStatus]

    def __post_init__(self):
        self.items = [
            item if isinstance(item, CartItem) else CartItem(**item)
            for item in self.items
        ]
