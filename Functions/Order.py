from dataclasses import asdict
from Entities.ItemStatus import ItemStatus
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Requests.CustomerCheckout import (
    CheckoutRequest,
    ReserveStockRequest,
    ReserveStockResponse,
)
from States.OrderState import OrderState

operator = Operator("order")

logger = getLogger(__name__)


# We should store a dictionary containing the next order_id and the order state
@operator.register
async def checkoutRequest(ctx: StatefulFunction, checkoutRequest: CheckoutRequest):
    data: dict = ctx.get()
    state = OrderState(**(data.get("state", {})))
    order_id = data.get("next_id", 1)
    state.checkouts.update({order_id: checkoutRequest})
    # TODO How do we get next order id?
    for idx, item in enumerate(checkoutRequest.items):
        reservation_event: ReserveStockRequest = ReserveStockRequest(
            order_id, item, idx
        )
        ctx.call_remote_async(
            "stock",
            "attempt_reserve_stock",
            f"{item.sellerId}:{item.productId}",
            (reservation_event, ctx.key),
        )
    ctx.put({"state": state, "next_id": order_id + 1})


@operator.register
async def TryReserveResponse(ctx: StatefulFunction, resp: ReserveStockResponse):
    order_id = resp.order_id
    data: dict = ctx.get()
    state = OrderState(**(data.get("state", {})))
    checkoutRequest: CheckoutRequest = state.checkouts[order_id]

    if resp.status == ItemStatus.IN_STOCK:
        if order_id in state.inStockItems.keys():
            state.inStockItems[order_id].append(resp.idx)
        else:
            state.inStockItems.update({order_id: [resp.idx]})

    # TODO check if all replies from stock are recieved

    data["state"] = asdict(state)
    ctx.put(data)


@operator.register
async def PaymentNotification(ctx: StatefulFunction):
    pass


@operator.register
async def ShipmentNotification(ctx: StatefulFunction):
    pass


@operator.register
async def GetOrders(ctx: StatefulFunction):
    # have to check if any state exists
    return ctx.get()
