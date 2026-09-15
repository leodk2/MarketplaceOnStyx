from dataclasses import dataclass


@dataclass(frozen=False)
class CartItem:
    sellerId: int
    productId: int
    productName: str
    unitPrice: float
    freightValue: float
    quantity: int
    voucher: float
    version: str
