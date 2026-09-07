from Entities.Shipment import ShipmentStatus
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus
from Entities.OrderItem import OrderItem
from Entities.PaymentType import PaymentStatus


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


@dataclass(frozen=True)
class InvoiceIssued:
    customer_checkout: CustomerCheckout
    order_id: int
    invoice_number: str
    items: list[OrderItem]
    issue_date: datetime
    total_invoice: float
    instance_id: str


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


@dataclass(frozen=True)
class ShipmentNotification:
    order_id: int
    shipment_status: ShipmentStatus
    event_date: datetime
    customer_id: int
