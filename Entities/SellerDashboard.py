from __future__ import annotations

from dataclasses import dataclass

from States.SellerState import OrderEntry


@dataclass(frozen=True, slots=True)
class OrderSellerView:
    seller_id: int
    count_orders: int
    count_items: int
    total_amount: float
    total_freight: float
    total_incentive: float
    total_invoice: float
    total_items: float


@dataclass(frozen=True, slots=True)
class SellerDashboard:
    seller_view: OrderSellerView
    order_entries: list[OrderEntry]
