from Entities.ItemStatus import ItemStatus
from pydantic import BaseModel


class ProductStatus(BaseModel):
    Id: int
    Status: ItemStatus
    UnitPrice: float = 0
    OldUnitPrice: float = 0
    QtyAvailable: int = 0
