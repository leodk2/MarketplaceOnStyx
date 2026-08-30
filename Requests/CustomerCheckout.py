from datetime import datetime
from typing import List
from Entities.CartItem import CartItem
from pydantic import BaseModel


class CustomerCheckout(BaseModel):
    CustomerId: int
    FirstName: str
    LastName: str
    Street: str
    Complement: str
    City: str
    State: str
    Zipcode: str
    PaymentType: str
    CardNumber: str
    CardHolderName: str
    CardExpiration: str
    CardSecurityNumber: str
    CardBrand: str
    Installments: int
    InstanceId: str


class CheckoutRequest(BaseModel):
    customerCheckout: CustomerCheckout
    items: List[CartItem]
    timestamp: datetime
    instanceId: str
