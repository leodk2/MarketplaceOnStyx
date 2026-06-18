from typing import List
from Entities.CartItem import CartItem
from Entities.ProductStatus import ProductStatus
from Entities.CartStatus import CartStatus
from pydantic import BaseModel


class Cart(BaseModel):
    CustomerId: int
    Status: CartStatus
    Items: List[CartItem]
    InstanceId: int
    Divergencies: List[ProductStatus]
