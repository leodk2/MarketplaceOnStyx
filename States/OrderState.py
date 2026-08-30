from Entities.Order import Order
from Entities.OrderItem import OrderItem
from Entities.OrderHistory import OrderHistory
from typing import Dict, List
from pydantic import BaseModel
from Requests.CustomerCheckout import CustomerCheckout

class OrderState(BaseModel):
    checkouts: Dict[int, CustomerCheckout]
    orders: Dict[int, Order]
    orderItems:Dict[int,OrderItem]
    orderHistory:Dict[int,OrderHistory]
    inStockItems:Dict[int, List[int]]
