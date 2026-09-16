import pickle
from Entities.TransactionMark import TransactionMark, TransactionType, MarkStatus
import itertools
import itertools
from Entities.SellerDashboard import OrderSellerView, SellerDashboard
from dataclasses import asdict
from logging import getLogger

from Requests.DeliveryNotification import DeliveryNotification
from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Order import OrderStatus
from Entities.Packages import PackageStatus
from Entities.SellerDashboard import OrderSellerView
from Entities.Shipment import ShipmentStatus
from Requests.CustomerCheckout import (
    InvoiceIssued,
    PaymentNotification,
    ShipmentNotification,
)
from States.SellerState import OrderEntry, SellerCompositeState, SellerState

seller_operator = Operator("seller", 4)

logger = getLogger(__name__)


class SellerExistsError(Exception):
    pass


@seller_operator.register
async def register_seller(ctx: StatefulFunction, seller):
    if ctx.get() is not None:
        raise SellerExistsError("error: seller already exists")
    state = SellerCompositeState(seller, SellerState())
    ctx.put(state)
    return ctx.key


@seller_operator.register
async def invoice_issued(ctx: StatefulFunction, invoice_dict: dict):
    invoice = InvoiceIssued(**invoice_dict)
    state = SellerCompositeState(**(ctx.get())).state

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
    state = SellerCompositeState(**(ctx.get()))

    id = f"{payment.customer_id}-{payment.order_id}"
    entries = state.state.order_entries.get(id)
    if entries is None:
        state.state.messagesReorderError.add(id)
        ctx.put(state)
        return ctx.key  # TODO what to return here?

    for entry in entries:
        entry.order_status = OrderStatus.PAYMENT_PROCESSED
    ctx.put(asdict(state))


@seller_operator.register
async def handle_delivery_notification(ctx: StatefulFunction, notif_dict: dict):
    state = SellerCompositeState(**(ctx.get()))
    notif = DeliveryNotification(**notif_dict)
    id = f"{notif.customer_id}-{notif.order_id}"
    entries = state.state.order_entries.get(id)
    if entries is None:
        state.state.messagesReorderError.add(id)
        ctx.put(asdict(state))
        return ctx.key

    target_entry = next((entry for entry in entries if entry.product_id == notif.product_id), None)

    if (target_entry is not None):
        target_entry.delivery_status = notif.package_status
        target_entry.delivery_date = notif.delivery_date
        target_entry.package_id = notif.package_id

    ctx.put(asdict(state))




@seller_operator.register
async def shipment_notification(ctx: StatefulFunction, notif_dict: dict):
    state = SellerCompositeState(**(ctx.get()))
    notif = ShipmentNotification(**notif_dict)

    id = f"{notif.customer_id}-{notif.order_id}"
    entries = state.state.order_entries.get(id)
    if entries is None:
        state.state.messagesReorderError.add(id)
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
        state.state.order_entries.pop(id)
    ctx.put(asdict(state))


@seller_operator.register
async def get_dashboard(ctx: StatefulFunction, req):
    # call shipment to get notifications that is still ongoing
    # From there call payment to get payments on those ongoing orders that hasn't failed(somehow) [listing 1]
    # call a new function on the seller_dashboard operator, that does the aggregations. [mix of listing 2 and 3]
    # return those aggregations.
    state = SellerState(**ctx.get())
    order_entries = list(
        itertools.chain.from_iterable([oe for oe in state.order_entries.values()])
    )
    mark: TransactionMark
    if len(state.order_entries) > 0:
        seller_view = OrderSellerView(
            ctx.key,
            len(state.order_entries),
            len(order_entries),
            sum(oe.total_amount for oe in order_entries),
            sum(oe.freight_value for oe in order_entries),
            sum(oe.total_incentive for oe in order_entries),
            sum(oe.total_invoice for oe in order_entries),
            sum(oe.total_items for oe in order_entries),
        )

        dashboard = {"sellerView": seller_view, "orderEntries": order_entries}
        # where to write the data?
        res = pickle.dumps(dashboard)
        mark = TransactionMark(
            req["tid"],
            TransactionType.QUERY_DASHBOARD,
            ctx.key,
            MarkStatus.SUCCESS,
            str(res),
        )
    else:
        mark = TransactionMark(
            req["tid"],
            TransactionType.QUERY_DASHBOARD,
            ctx.key,
            MarkStatus.SUCCESS,
            "seller",
        )

    return mark
