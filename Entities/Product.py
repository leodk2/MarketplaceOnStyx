from dataclasses import dataclass


@dataclass
class Product:
    seller_id: int
    product_id: int
    price: float
    freight_value: float
    version: str
    name: str = ""
    sku: str = ""
    category: str = ""
    description: str = ""
    status: str = "approved"
