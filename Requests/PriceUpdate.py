from dataclasses import dataclass


@dataclass(frozen=True)
class UpdatePriceEvent:
    sellerId: int
    productId: int
    price: float
    version: str
    instanceId: str
