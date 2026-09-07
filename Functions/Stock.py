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
async def attempt_reserve_stock(ctx: StatefulFunction, item_dict: dict, caller_id):
    item = ReserveStockRequest(**item_dict)
    cart_item: CartItem = item.cartItem

    status = get_stock_status(ctx, cart_item.quantity, cart_item.version)

    response = ReserveStockResponse(
        item.orderId, cart_item.sellerId, cart_item.productId, status, item.idx
    )
    ctx.call_remote_async("order", "try_reserve_response", caller_id, (response,))


@stock_operator.register
async def payment_confirmed(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentStockEvent(**payment_dict)
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
class StockItemDoesNotExist(Exception):
    pass
class StockItemAlreadyExists(Exception):
    pass


@stock_operator.register
async def on_product_update(ctx: StatefulFunction, newVersion: str) -> StockItem:
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")
    state['Version'] = newVersion
    ctx.put(state)
    return ctx.get()

@stock_operator.register
async def create_stock(ctx: StatefulFunction, stock_item: StockItem) -> StockItem:
    state = ctx.get()
    if state is not None:
        raise StockItemAlreadyExists(f"Error: StockItem with id {ctx.key} already exists")
    ctx.put(stock_item)
    return stock_item

@stock_operator.register
async def get_stock(ctx: StatefulFunction) -> StockItem:
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")
    return state
