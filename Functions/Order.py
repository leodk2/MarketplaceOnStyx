import itertools
from dataclasses import asdict
from datetime import datetime, timedelta
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.CartItem import CartItem
from Entities.ItemStatus import ItemStatus
from Entities.Order import Order, OrderStatus
from Entities.OrderHistory import OrderHistory
from Entities.OrderItem import OrderItem
from Requests.CustomerCheckout import (
    CheckoutRequest,
    InvoiceIssued,
    PaymentNotification,
    ReserveStockRequest,
    ReserveStockResponse,
    ShipmentNotification,
    ShipmentStatus,
)
from States.OrderState import OrderState

# keyed by customer id which  is the same as cart id
order_operator = Operator("order")

logger = getLogger(__name__)


class OrderNotFoundException(Exception):
    pass


# We should store a dictionary containing the next order_id and the order state
@order_operator.register
async def checkout_request(ctx: StatefulFunction, checkoutRequest_dict: dict):
    checkoutRequest: CheckoutRequest = CheckoutRequest(**checkoutRequest_dict)
    data: dict = ctx.get()
    state = OrderState(**(data.get("state", {})))
    order_id = data.get("next_id", 1)
    state.checkouts.update({order_id: checkoutRequest})
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


@order_operator.register
async def try_reserve_response(ctx: StatefulFunction, resp_dict: dict):
    resp = ReserveStockResponse(**resp_dict)
    order_id = resp.order_id
    data: dict = ctx.get()
    state = OrderState(**(data.get("state", {})))
    checkoutRequest: CheckoutRequest = state.checkouts[order_id]

    if resp.status == ItemStatus.IN_STOCK:
        if order_id in state.inStockItems:
            state.inStockItems[order_id].append(resp.idx)
        else:
            state.inStockItems.update({order_id: [resp.idx]})

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
        seller_invoice = InvoiceIssued(
            checkoutRequest.customerCheckout,
            order_id,
            invoice_number,
            list(ois),
            now,
            order.totalInvoice,
            checkoutRequest.instanceId,
        )  # TODO create invoice with order_items for a specific seller here

        ctx.call_remote_async(
            "seller", "invoice_issued", seller_id, (asdict(seller_invoice),)
        )

    payment_invoice = InvoiceIssued(
        checkoutRequest.customerCheckout,
        order_id,
        invoice_number,
        order_items,
        now,
        order.totalInvoice,
        checkoutRequest.instanceId,
    )  # TODO create invoice with order_items for a specific seller here
    ctx.call_remote_async(
        "payment", "invoice_issued", ctx.key, (asdict(payment_invoice),)
    )


@order_operator.register
async def payment_notification(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentNotification(**payment_dict)
    now = datetime.now()
    state: OrderState = OrderState(**(ctx.get()["state"]))
    next_id = ctx.get()["next_id"]

    order_id = payment.order_id

    history: OrderHistory = OrderHistory(order_id, now, OrderStatus.PAYMENT_PROCESSED)
    state.orderHistory[order_id].append(history)

    order: Order = state.orders[order_id]
    order.orderStatus = OrderStatus.PAYMENT_PROCESSED
    order.updatedAt = now
    ctx.put({"next_id": next_id, "state": state})


@order_operator.register
async def shipment_notification(ctx: StatefulFunction, notif_dict: dict):
    state = OrderState(**(ctx.get()["state"]))
    notif: ShipmentNotification = ShipmentNotification(**notif_dict)

    order_id = notif.order_id
    order = state.orders.get(order_id, None)
    if order is None:
        raise OrderNotFoundException(
            f"Error: order {order_id} cannot be found to update to status in function {ctx.key}. Current state size is {len(state.orders)}"
        )

    now = datetime.now()

    status = OrderStatus.READY_FOR_SHIPMENT
    if notif.shipment_status is ShipmentStatus.DELIVERY_IN_PROGRESS:
        status = OrderStatus.IN_TRANSIT
    elif notif.shipment_status is ShipmentStatus.CONCLUDED:
        status = OrderStatus.DELIVERED

    history = OrderHistory(order_id, now, status)

    state.orderHistory[order_id].append(history)

    order.updatedAt = now
    order.orderStatus = status
    if status is OrderStatus.DELIVERED:
        order.deliveredCustomerDate = notif.event_date

        # more logging to postgres

        state.clean_state(order_id)


@order_operator.register
async def GetOrders(ctx: StatefulFunction):
    # have to check if any state exists
    return ctx.get()
