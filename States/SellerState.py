from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from Entities.Order import OrderStatus
from Entities.Packages import PackageStatus
from Entities.Seller import Seller


@dataclass(init=True)
class SellerCompositeState:
    seller_entity: Seller
    state: SellerState

    def __post_init__(self):
        if not isinstance(self.seller_entity, Seller):
            self.seller_entity = Seller(**self.seller_entity)
        if not isinstance(self.state, SellerState):
            self.state = SellerState(**self.state)


@dataclass
class SellerState:
    order_entries: dict[str, list[OrderEntry]] = field(default_factory=dict)
    messagesReorderError: set[str] = field(default_factory=set)

    def __post_init__(self):
        self.order_entries = {
            key: [
                entry if isinstance(entry, OrderEntry) else OrderEntry(**entry)
                for entry in entries
            ]
            for key, entries in self.order_entries.items()
        }
        self.messagesReorderError = set(self.messagesReorderError)


@dataclass
class OrderEntry:
    seller_id: int
    order_id: int
    package_id: int | None
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
    delivery_status: PackageStatus | None
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
        package_id: int | None = None,
        shipment_date: date | None = None,
        delivery_date: date | None = None,
        delivery_status: PackageStatus | None = None,
        product_category: str = "",
    ):
        self.seller_id = seller_id
        self.order_id = order_id
        self.package_id = package_id
        self.product_id = product_id
        self.product_name = product_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.total_items = total_items
        self.total_amount = total_amount
        self.total_invoice = total_invoice
        self.total_incentive = total_incentive
        self.freight_value = freight_value
        self.shipment_date = shipment_date
        self.delivery_date = delivery_date
        self.order_status = order_status
        self.delivery_status = delivery_status
        self.product_category = product_category
