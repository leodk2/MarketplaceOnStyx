from dataclasses import dataclass
from typing import List
from Entities.CartItem import CartItem
from Entities.ProductStatus import ProductStatus
from Entities.CartStatus import CartStatus


@dataclass
class Cart:
    CustomerId: int
    Status: CartStatus
    Items: List[CartItem]
    InstanceId: int
    Divergencies: List[ProductStatus]
