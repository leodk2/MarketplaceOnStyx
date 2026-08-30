from datetime import datetime
from pydantic import BaseModel

class OrderItem(BaseModel):
    orderId: int
    orderItemId:int
    productId: int
    productName: str
    sellerId:int
    unitPrice:float
    frieghtValue:float
    quantity:int
    totalPrice:float
    totalAmount:float
    voucher:float
    shippingLimitDate:datetime
    
    
