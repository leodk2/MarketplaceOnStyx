from dataclasses import asdict
from datetime import datetime
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus
from Entities.PaymentType import PaymentStatus
from Entities.StockItem import StockItem
from Entities.TransactionMark import MarkStatus, TransactionMark, TransactionType
from Requests.CustomerCheckout import (
    PaymentStockEvent,
    ReserveStockRequest,
    ReserveStockResponse,
)
from TransactionMarkException import TransactionMarkException

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
    ctx.call_remote_async("order", "try_reserve_response", caller_id, (asdict(response),))


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


class StockItemAlreadyExists(Exception):
    pass


@stock_operator.register
async def on_product_update(ctx: StatefulFunction, newVersion: str) -> dict:
    state = ctx.get()
    if state is None: 
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")
    stockitem: StockItem = StockItem(**state)
    stockitem.version = newVersion
    ctx.put(asdict(stockitem))
    return TransactionMark(
        state["version"],
        TransactionType.UPDATE_PRODUCT,
        seller_id,
        MarkStatus.SUCCESS,
        "stock",
    )
   

@stock_operator.register
async def create_stock(ctx: StatefulFunction, stock_item: dict) -> dict:
    state = ctx.get()
    if state is not None:
        raise StockItemAlreadyExists(
            f"Error: StockItem with id {ctx.key} already exists"
        )
    ctx.put(stock_item)
    return stock_item


@stock_operator.register
async def get_stock(ctx: StatefulFunction) -> dict:
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(
            f"Error: StockItem with id {ctx.key} does not exist"
        )
    return state

@stock_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@stock_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state

@stock_operator.register
async def stock_payment(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentStockEvent(**payment_dict)
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")

    stockItem: StockItem = StockItem(**state)

    if payment.status is PaymentStatus.SUCCEEDED:
        stockItem.confirm_reservation(payment.quantity)
    else:
        stockItem.cancel_reservation(payment.quantity)

    stockItem.updated_at = datetime.now()

    ctx.put(asdict(stockItem))