from dataclasses import dataclass

from Entities.Order import Order
from Entities.OrderHistory import OrderHistory
from Entities.OrderItem import OrderItem
from Requests.CustomerCheckout import CheckoutRequest


@dataclass
class OrderState:
    checkouts: dict[int, CheckoutRequest]
    orders: dict[int, Order]
    orderItems: dict[int, OrderItem]
    orderHistory: dict[int, OrderHistory]
    inStockItems: dict[int, list[int]]
