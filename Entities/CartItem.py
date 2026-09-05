from dataclasses import dataclass

@dataclass
class CartItem:
    SellerId: int
    ProductId: int
    ProductName: str
    UnitPrice: float
    FreightValue: float
    Quantity: int
    Voucher: float
    Version: str
