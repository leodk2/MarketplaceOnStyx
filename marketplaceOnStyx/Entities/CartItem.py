from pydantic import BaseModel


class CartItem(BaseModel):
    SellerId: int
    ProductId: int
    ProductName: str
    UnitPrice: float
    FreightValue: float
    Quantity: int
    Voucher: float
    Version: str
