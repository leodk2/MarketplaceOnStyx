from dataclasses import asdict
from logging import getLogger

from Requests.DeliveryNotification import DeliveryNotification
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
async def invoice_issued(ctx: StatefulFunction, invoice_dict: dict):
    invoice = InvoiceIssued(**invoice_dict)
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
async def payment_notification(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentNotification(**payment_dict)
    state = SellerState(**(ctx.get()))

    id = f"{payment.customer_id}-{payment.order_id}"
    entries = state.order_entries.get(id)
    if entries is None:
        state.messagesReorderError.add(id)
        ctx.put(state)
        return ctx.key

    for entry in entries:
        entry.order_status = OrderStatus.PAYMENT_PROCESSED
    ctx.put(asdict(state))


@seller_operator.register
async def handle_delivery_notification(ctx: StatefulFunction, notif_dict: dict):
    state = SellerState(**(ctx.get()))
    notif = DeliveryNotification(**notif_dict)
    id = f"{notif.customer_id}-{notif.order_id}"

    entries = state.order_entries.get(id)
    if entries is None:
        state.messagesReorderError.add(id)
        ctx.put(asdict(state))
        return ctx.key 

    target_entry = next((entry for entry in entries if entry.product_id == notif.product_id), None)

    if (target_entry is not None):
        target_entry.delivery_status = notif.package_status
        target_entry.delivery_date = notif.delivery_date
        target_entry.package_id = notif.package_id

    ctx.put(asdict(state))



    
