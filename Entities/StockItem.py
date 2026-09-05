from dataclasses import dataclass

@dataclass
class StockItem:
    SellerId: int
    ProductId: int
    QtyAvailable: int
    QtyReserved: int
    OrderCount: int
    data: str
    version: str