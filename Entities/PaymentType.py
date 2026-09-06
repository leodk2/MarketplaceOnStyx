from enum import Enum


class PaymentType(Enum):
    CREDIT_CARD = 0
    BOLETO = 1
    VOURCHER = 2
    DEBIT_CARD = 3


class PaymentStatus(Enum):
    REQUIRES_PAYMENT_METHOD = 0
    SUCCEEDED = 1
    CANCELED = 2
