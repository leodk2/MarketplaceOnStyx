from dataclasses import dataclass, field

from Entities.Order import Order
from Entities.OrderHistory import OrderHistory
from Entities.OrderItem import OrderItem
from Requests.CustomerCheckout import CheckoutRequest


@dataclass
class OrderState:
    checkouts: dict[int, CheckoutRequest] = field(default_factory=dict)
    orders: dict[int, Order] = field(default_factory=dict)
    orderItems: dict[int, list[OrderItem]] = field(default_factory=dict)
    orderHistory: dict[int, list[OrderHistory]] = field(default_factory=dict)
    inStockItems: dict[int, list[int]] = field(default_factory=dict)
    remainingAcksMap: dict[int, int] = field(default_factory=dict)

    def __post_init__(self):
        self.checkouts = {
            order_id: (checkout if isinstance(checkout, CheckoutRequest) else CheckoutRequest(**checkout))
            for order_id, checkout in self.checkouts.items()
        }
        self.orders = {
            order_id: (order if isinstance(order, Order) else Order(**order))
            for order_id, order in self.orders.items()
        }

    def set_remaining_acks(self, order_id: int, item_count: int):
        if not order_id in self.remainingAcksMap:
            self.remainingAcksMap.update({order_id: item_count})

    def unset_remaining_acks(self, order_id: int):
        if order_id in self.remainingAcksMap:
            self.remainingAcksMap.pop(order_id)

    def decrease_remaining_acks(self, order_id: int) -> int | None:
        if order_id in self.remainingAcksMap:
            self.remainingAcksMap[order_id] -= 1
            return self.remainingAcksMap[order_id]
        return None

    def add_order(
        self,
        order_id: int,
        order: Order,
        items: list[OrderItem],
        order_history: OrderHistory,
    ):
        self.orders.update({order_id: order})
        self.orderItems.update({order_id: items})
        history: list[OrderHistory] = []
        if order_id in self.orderHistory:
            history = self.orderHistory[order_id]
        else:
            self.orderHistory.update({order_id: history})

        history.append(order_history)

    def clean_state(self, order_id: int):
        self.checkouts.pop(order_id)
        self.inStockItems.pop(order_id)
        self.orderHistory.pop(order_id)
        self.orders.pop(order_id)
        self.orderItems.pop(order_id)
