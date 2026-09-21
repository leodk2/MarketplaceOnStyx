from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus
from Entities.OrderItem import OrderItem
from Entities.PaymentType import PaymentStatus
from Entities.Shipment import ShipmentStatus


@dataclass(frozen=True)
class CustomerCheckout:
    CustomerId: int
    FirstName: str
    LastName: str
    Street: str
    Complement: str
    City: str
    State: str
    ZipCode: str
    PaymentType: str
    CardNumber: str
    CardHolderName: str
    CardExpiration: str
    CardSecurityNumber: str
    CardBrand: str
    Installments: int
    instanceId: str


@dataclass(frozen=True)
class CheckoutRequest:
    customerCheckout: CustomerCheckout
    items: list[CartItem]
    timestamp: datetime
    instanceId: str

    def __post_init__(self):
        if not isinstance(self.customerCheckout, CustomerCheckout):
            object.__setattr__(
                self, "customerCheckout", CustomerCheckout(**self.customerCheckout)
            )
        object.__setattr__(
            self,
            "items",
            [
                item if isinstance(item, CartItem) else CartItem(**item)
                for item in self.items
            ],
        )


@dataclass(frozen=True, slots=True)
class ReserveStockRequest:
    orderId: int
    cartItem: CartItem
    idx: int

    def __post_init__(self):
        if not isinstance(self.cartItem, CartItem):
            object.__setattr__(self, "cartItem", CartItem(**self.cartItem))


@dataclass(frozen=True)
class ReserveStockResponse:
    order_id: int
    seller_id: int
    product_id: int
    status: ItemStatus
    idx: int


@dataclass(frozen=True)
class InvoiceIssued:
    customer_checkout: CustomerCheckout
    order_id: int
    invoice_number: str
    items: list[OrderItem]
    issue_date: datetime
    total_invoice: float
    instance_id: str

    def __post_init__(self):
        if not isinstance(self.customer_checkout, CustomerCheckout):
            object.__setattr__(
                self, "customer_checkout", CustomerCheckout(**self.customer_checkout)
            )
        object.__setattr__(
            self,
            "items",
            [
                item if isinstance(item, OrderItem) else OrderItem(**item)
                for item in self.items
            ],
        )


@dataclass(frozen=True)
class PaymentStockEvent:
    quantity: int
    status: PaymentStatus


@dataclass(frozen=True)
class PaymentNotification:
    order_id: int
    customer_id: int
    status: PaymentStatus


class CustomerNotificationType(Enum):
    NOTIFY_FAILED_PAYMENT = 0
    NOTIFY_SUCCESS_PAYMENT = 1
    NOTIFY_FAILED_CHECKOUT = 2


@dataclass(frozen=True)
class PaymentConfirmed:
    customer_checkout: CustomerCheckout
    order_id: int
    total_amount: float
    items: list[OrderItem]
    date: datetime
    instance_id: str

    def __post_init__(self):
        if not isinstance(self.customer_checkout, CustomerCheckout):
            object.__setattr__(
                self, "customer_checkout", CustomerCheckout(**self.customer_checkout)
            )
        object.__setattr__(
            self,
            "items",
            [
                item if isinstance(item, OrderItem) else OrderItem(**item)
                for item in self.items
            ],
        )


@dataclass(frozen=True)
class ShipmentNotification:
    order_id: int
    shipment_status: ShipmentStatus
    event_date: datetime
    customer_id: int
