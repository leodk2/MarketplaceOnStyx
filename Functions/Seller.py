from dataclasses import asdict
from logging import getLogger

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Order import OrderStatus
from Requests.CustomerCheckout import InvoiceIssued, PaymentNotification
from States.SellerState import OrderEntry, SellerState

seller = Operator("seller", 4)

logger = getLogger(__name__)


@seller.register
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


@seller.register
def payment_notification(ctx: StatefulFunction, payment: PaymentNotification):
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
