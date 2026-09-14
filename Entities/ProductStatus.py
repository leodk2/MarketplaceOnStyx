from dataclasses import dataclass

from Entities.ItemStatus import ItemStatus


@dataclass
class ProductStatus:
    Id: int
    Status: ItemStatus
    UnitPrice: float = 0
    OldUnitPrice: float = 0
    QtyAvailable: int = 0
