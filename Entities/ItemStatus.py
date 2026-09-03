from enum import Enum


class ItemStatus(Enum):
    DELETED = 0
    OUT_OF_STOCK = 1
    PRICE_DIVERGENCE = 2
    IN_STOCK = 3
    UNKNOWN = 4
    UNAVAILABLE = 5
