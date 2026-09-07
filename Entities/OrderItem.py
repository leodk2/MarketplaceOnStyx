from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderItem:
    orderId: int
    orderItemId: int
    productId: int
    productName: str
    sellerId: int
    unitPrice: float
    freightValue: float
    quantity: int
    totalPrice: float
    totalAmount: float
    voucher: float
    shippingLimitDate: datetime
