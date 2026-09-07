from dataclasses import dataclass

from Entities.Order import Order
from Entities.OrderHistory import OrderHistory
from Entities.OrderItem import OrderItem
from Requests.CustomerCheckout import CheckoutRequest


@dataclass
class OrderState:
    checkouts: dict[int, CheckoutRequest]
    orders: dict[int, Order]
    orderItems: dict[int, list[OrderItem]]
    orderHistory: dict[int, list[OrderHistory]]
    inStockItems: dict[int, list[int]]
    remainingAcksMap: dict[int, int]

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
