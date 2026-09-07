from dataclasses import dataclass
from datetime import date

from Entities.Order import OrderStatus
from Entities.Packages import PackageStatus


@dataclass
class SellerState:
    order_entries: dict[str, list[OrderEntry]] = {}
    messagesReorderError: set[str] = set()


@dataclass
class OrderEntry:
    seller_id: int
    order_id: int
    package_id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    total_items: float
    total_amount: float
    total_invoice: float
    total_incentive: float
    freight_value: float
    shipment_date: date | None
    delivery_date: date | None
    order_status: OrderStatus
    delivery_status: PackageStatus
    product_category: str = ""

    def __init__(
        self,
        order_id: int,
        seller_id: int,
        product_id: int,
        product_name: str,
        quantity: int,
        total_amount: float,
        total_invoice: float,
        total_items: float,
        total_incentive: float,
        freight_value: float,
        unit_price: float,
        order_status: OrderStatus,
    ):
        self.seller_id = seller_id
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.total_items = total_items
        self.total_amount = total_amount
        self.total_invoice = total_invoice
        self.total_incentive = total_incentive
        self.freight_value = freight_value
        self.order_status = order_status
