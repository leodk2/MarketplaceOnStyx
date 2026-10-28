from __future__ import annotations

from dataclasses import dataclass, field

from Entities.Seller import Seller
from Entities.SellerDashboard import SellerDashboard
from States.OrderEntry import OrderEntry


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
    seller_dashboard: SellerDashboard | None = None
    should_refresh_dashboard: bool = True

    def __post_init__(self):
        self.order_entries = {
            key: [
                entry if isinstance(entry, OrderEntry) else OrderEntry(**entry)
                for entry in entries
            ]
            for key, entries in self.order_entries.items()
        }
        self.messagesReorderError = set(self.messagesReorderError)
