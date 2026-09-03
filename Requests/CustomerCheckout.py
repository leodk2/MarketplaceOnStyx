from dataclasses import dataclass
from datetime import datetime

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus


@dataclass(frozen=True)
class CustomerCheckout:
    customerId: int
    firstName: str
    lastName: str
    street: str
    complement: str
    city: str
    state: str
    zipcode: str
    paymentType: str
    cardNumber: str
    cardHolderName: str
    cardExpiration: str
    cardSecurityNumber: str
    cardBrand: str
    installments: int
    instanceId: str


@dataclass(frozen=True)
class CheckoutRequest:
    customerCheckout: CustomerCheckout
    items: list[CartItem]
    timestamp: datetime
    instanceId: str


@dataclass(frozen=True, slots=True)
class ReserveStockRequest:
    orderId: int
    cartItem: CartItem
    idx: int


@dataclass(frozen=True)
class ReserveStockResponse:
    order_id: int
    seller_id: int
    product_id: int
    status: ItemStatus
    idx: int
