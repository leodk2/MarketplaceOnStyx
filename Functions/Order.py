import itertools
from Entities.OrderHistory import OrderHistory
from Entities.OrderItem import OrderItem
from Entities.Order import Order, OrderStatus
from Entities.CartItem import CartItem
from datetime import datetime, timedelta
from dataclasses import asdict
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.ItemStatus import ItemStatus
from Requests.CustomerCheckout import (
    CheckoutRequest,
    ReserveStockRequest,
    ReserveStockResponse,
)
from States.OrderState import OrderState

# keyed by customer id which  is the same as cart id
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
    state.set_remaining_acks(order_id, len(checkoutRequest.items))
    ctx.put({"state": state, "next_id": order_id + 1})


@operator.register
async def TryReserveResponse(ctx: StatefulFunction, resp: ReserveStockResponse):
    order_id = resp.order_id
    data: dict = ctx.get()
    state = OrderState(**(data.get("state", {})))
    checkoutRequest: CheckoutRequest = state.checkouts[order_id]

    if resp.status == ItemStatus.IN_STOCK:
        if order_id in state.inStockItems:
            state.inStockItems[order_id].append(resp.idx)
        else:
            state.inStockItems.update({order_id: [resp.idx]})

    # TODO check if all replies from stock are recieved

    if state.decrease_remaining_acks(order_id) == 0:
        state.unset_remaining_acks(order_id)
        if order_id in state.inStockItems:
            generate_order(ctx, checkoutRequest, state, order_id)
            state.checkouts.pop(order_id)

        else:
            # Do we need transaction marks, and egress messages?
            # Maybe that would just be a return of this workflow?

            state.clean_state(order_id)

    data["state"] = asdict(state)
    ctx.put(data)


def generate_order(
    ctx: StatefulFunction,
    checkoutRequest: CheckoutRequest,
    order_state: OrderState,
    order_id: int,
):
    now = datetime.now()
    items_to_checkout: list[CartItem] = []
    for idx in range(len(order_state.inStockItems[order_id])):
        items_to_checkout.append(checkoutRequest.items[idx])
    total_freight = 0
    total_amount = 0
    for item in items_to_checkout:
        total_freight += item.freightValue
        total_amount += item.unitPrice * item.quantity
    total_items = total_amount

    totalPerItem: dict[tuple[int, int], float] = {}

    total_incentive: float = 0
    for item in items_to_checkout:
        total_item = item.unitPrice * item.quantity

        if total_item - item.voucher > 0:
            total_amount -= item.voucher
            total_incentive += item.voucher
            total_item -= item.voucher
        else:
            total_amount -= total_item
            total_incentive += total_item
            total_item = 0

        totalPerItem.update({(item.sellerId, item.productId): total_item})
    customer_id = checkoutRequest.customerCheckout.customerId

    invoice_number = f"{customer_id}-{now}-{order_id}"
    order: Order = Order(
        order_id,
        customer_id,
        OrderStatus.INVOICED,
        invoice_number,
        checkoutRequest.timestamp,
        None,
        None,
        None,
        len(checkoutRequest.items),
        total_amount,
        total_freight,
        total_incentive,
        total_amount + total_freight,
        total_items,
        "",
    )

    order_items: list[OrderItem] = []
    id: int = 1

    for item in items_to_checkout:
        order_items.append(
            OrderItem(
                order_id,
                id,
                item.productId,
                item.productName,
                item.sellerId,
                item.unitPrice,
                item.freightValue,
                item.quantity,
                item.unitPrice * item.quantity,
                totalPerItem[(item.sellerId, item.productId)],
                item.voucher,
                now + timedelta(3),
            )
        )
        id += 1
    order_history: OrderHistory = OrderHistory(order_id, now, OrderStatus.INVOICED)

    order_state.add_order(order_id, order, order_items, order_history)

    items_per_seller = itertools.groupby(order_items, lambda oi: oi.sellerId)

    for seller_id, ois in items_per_seller:
        invoice = (
            object()
        )  # TODO create invoice with order_items for a specific seller here

        ctx.call_remote_async("seller", "invoice_issued", seller_id, (invoice,))

    invoice = object()  # TODO create invoice with all order_items here
    ctx.call_remote_async("payment", "invoice_issued", ctx.key, (invoice,))


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
