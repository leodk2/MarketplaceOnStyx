from enum import Enum


class PaymentType(Enum):
    CREDIT_CARD = 0
    BOLETO = 1
    VOURCHER = 2
    DEBIT_CARD = 3
