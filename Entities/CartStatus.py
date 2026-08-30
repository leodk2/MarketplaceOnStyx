from enum import Enum


class CartStatus(Enum):
    OPEN = 1
    CHECKOUT_SENT = 2
    PRODUCT_DIVERGENCE = 3
