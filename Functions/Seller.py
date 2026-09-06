from dataclasses import asdict
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Order import OrderStatus
from Entities.Packages import PackageStatus
from Entities.Shipment import ShipmentStatus
from Requests.CustomerCheckout import (
    InvoiceIssued,
    PaymentNotification,
    ShipmentNotification,
)
from States.SellerState import OrderEntry, SellerState

seller_operator = Operator("seller", 4)

logger = getLogger(__name__)


@seller_operator.register
async def register_seller(ctx: StatefulFunction, seller):
    ctx.put(seller)
    return ctx.key


@seller_operator.register
async def invoice_issued(ctx: StatefulFunction, invoice: InvoiceIssued):
    state = SellerState(**(ctx.get()))

    order_items = invoice.items
    seller_id = ctx.key

    order_entries: list[OrderEntry] = []

    state.order_entries.update(
        {f"{invoice.customer_checkout.customerId}-{invoice.order_id}": order_entries}
    )

    for oi in order_items:
        order_entry = OrderEntry(
            invoice.order_id,
            seller_id,
            oi.productId,
            oi.productName,
            oi.quantity,
            oi.totalAmount,
            oi.totalPrice,
            oi.totalAmount + oi.freightValue,
            oi.voucher,
            oi.freightValue,
            oi.unitPrice,
            OrderStatus.INVOICED,
        )
    order_entries.append(order_entry)

    ctx.put(asdict(state))


@seller_operator.register
async def payment_notification(ctx: StatefulFunction, payment: PaymentNotification):
    state = SellerState(**(ctx.get()))

    id = f"{payment.customer_id}-{payment.order_id}"
    entries = state.order_entries.get(id)
    if entries is None:
        state.messagesReorderError.add(id)
        ctx.put(state)
        return ctx.key  # TODO what to return here?

    for entry in entries:
        entry.order_status = OrderStatus.PAYMENT_PROCESSED
    ctx.put(asdict(state))


@seller_operator.register
async def shipment_notification(ctx: StatefulFunction, notif_dict: dict):
    state = SellerState(**(ctx.get()))
    notif = ShipmentNotification(**notif_dict)

    id = f"{notif.customer_id}-{notif.order_id}"
    entries = state.order_entries.get(id)
    if entries is None:
        state.messagesReorderError.add(id)
        ctx.put(asdict(state))
        return ctx.key  # TODO what to return here?

    for entry in entries:
        if notif.shipment_status is ShipmentStatus.APPROVED:
            entry.order_status = OrderStatus.READY_FOR_SHIPMENT
            entry.shipment_date = notif.event_date
            entry.delivery_status = PackageStatus.READY_TO_SHIP
        elif notif.shipment_status is ShipmentStatus.DELIVERY_IN_PROGRESS:
            entry.order_status = OrderStatus.IN_TRANSIT
            entry.delivery_status = PackageStatus.SHIPPED
        elif notif.shipment_status is ShipmentStatus.CONCLUDED:
            entry.order_status = OrderStatus.DELIVERED

    if notif.shipment_status is ShipmentStatus.CONCLUDED:
        state.order_entries.pop(id)
    ctx.put(asdict(state))
