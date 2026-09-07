from dataclasses import dataclass

@dataclass
class Product:
    SellerId: int
    ProductId: int
    Price: float
    FreightValue: float
    Version: str
    Name: str = ""
    Sku: str = ""
    Category: str = ""
    Description: str = ""
    Status: str = "approved"
