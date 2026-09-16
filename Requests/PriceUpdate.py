from dataclasses import dataclass


@dataclass(frozen=True)
class UpdatePriceEvent:
    seller_id: int
    product_id: int
    instance_id: str
    price: float
