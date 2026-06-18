from pydantic import BaseModel


class Product(BaseModel):
    SellerId: int
    ProductId: int
    Name: str = ""
    Sku: str = ""
    Category: str = ""
    Description: str = ""
    Price: float
    FreightValue: float
    Status: str = "approved"
    Version: str
