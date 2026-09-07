from Entities.PaymentType import PaymentType, PaymentStatus
from dataclasses import dataclass


@dataclass
class OrderPayment:
    order_id: int
    sequential: int
    type: PaymentType
    installments: int
    value: float
    status: PaymentStatus


@dataclass
class OrderPaymentCard:
    order_id: int
    payment_sequential: int
    card_number: str
    card_holder_name: str
    card_expiration: str
    card_brand: str
