from dataclasses import asdict
from Entities.PaymentType import PaymentStatus
from datetime import datetime
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus
from Entities.StockItem import StockItem
from Requests.CustomerCheckout import (
    PaymentStockEvent,
    ReserveStockRequest,
    ReserveStockResponse,
)

stock_operator = Operator("stock", composite_key_hash_params=(0, ":"))
# composite key of seller_id:product_id
logger = getLogger(__name__)


@stock_operator.register
async def attempt_reserve_stock(
    ctx: StatefulFunction, item: ReserveStockRequest, caller_id
):
    cart_item: CartItem = item.cartItem

    status = get_stock_status(ctx, cart_item.quantity, cart_item.version)

    response = ReserveStockResponse(
        item.orderId, cart_item.sellerId, cart_item.productId, status, item.idx
    )
    ctx.call_remote_async("order", "TryReserve", caller_id, (response,))

    return ""


@stock_operator.register
async def payment_confirmed(ctx: StatefulFunction, payment: PaymentStockEvent):
    state = StockItem(**(ctx.get()))

    if payment.status is PaymentStatus.SUCCEEDED:
        state.confirm_reservation(payment.quantity)
    else:
        state.cancel_reservation(payment.quantity)
    # handle this key not having a stock item
    state.updated_at = datetime.now()

    ctx.put(asdict(state))


def get_stock_status(ctx: StatefulFunction, quantity: int, version: str) -> ItemStatus:
    state = ctx.get()
    if state is None:
        return ItemStatus.UNKNOWN
    stockItem: StockItem = StockItem(**state)
    if version != stockItem.version:
        return ItemStatus.UNAVAILABLE
    if stockItem.qty_reserved + quantity > stockItem.qty_available:
        return ItemStatus.OUT_OF_STOCK

    stockItem.reserve(quantity)
    stockItem.updated_at = datetime.now()

    ctx.put(asdict(stockItem))

    return ItemStatus.IN_STOCK
