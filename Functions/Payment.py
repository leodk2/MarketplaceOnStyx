from dataclasses import asdict
from datetime import datetime

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.CustomerNotificationType import CustomerNotificationType
from Entities.OrderPayment import OrderPayment, OrderPaymentCard
from Entities.PaymentType import PaymentStatus, PaymentType
from Requests.CustomerCheckout import (
    CustomerCheckout,
    InvoiceIssued,
    PaymentConfirmed,
    PaymentNotification,
    PaymentStockEvent,
)

payment = Operator("payment", 4)


@payment.register
async def invoice_issued(ctx: StatefulFunction, invoice: InvoiceIssued):
    customer_checkout: CustomerCheckout = invoice.customer_checkout

    now: datetime = datetime.now()

    order_id = invoice.order_id

    seq: int = 1
    is_credit_card: bool = customer_checkout.paymentType is PaymentType.CREDIT_CARD.name

    order_payments: list[OrderPayment] = []  # noqa: F821
    card: OrderPaymentCard

    if is_credit_card or (customer_checkout.paymentType is PaymentType.DEBIT_CARD.name):
        card_payment_line = OrderPayment(
            order_id,
            seq,
            PaymentType.CREDIT_CARD if is_credit_card else PaymentType.DEBIT_CARD,
            customer_checkout.installments,
            invoice.total_invoice,
            PaymentStatus.SUCCEEDED,
        )
        # this is not used in the tstatefun implementation. Do we need it?
        card = OrderPaymentCard(
            order_id,
            seq,
            customer_checkout.cardNumber,
            customer_checkout.cardHolderName,
            customer_checkout.cardExpiration,
            customer_checkout.cardBrand,
        )
        order_payments.append(card_payment_line)
        seq += 1

    if invoice.customer_checkout.paymentType is PaymentType.BOLETO.name:
        order_payments.append(
            OrderPayment(
                order_id,
                seq,
                PaymentType.BOLETO,
                1,
                invoice.total_invoice,
                PaymentStatus.SUCCEEDED,
            )
        )
        seq += 1

    for oi in invoice.items:
        if oi.voucher > 0:
            order_payments.append(
                OrderPayment(
                    order_id,
                    seq,
                    PaymentType.VOURCHER,
                    1,
                    oi.voucher,
                    PaymentStatus.SUCCEEDED,
                )
            )
            seq += 1
    # tstatefun logs the payment to postgres. Do we need to?

    for oi in invoice.items:
        stock_payment_event = PaymentStockEvent(oi.quantity, PaymentStatus.SUCCEEDED)
        ctx.call_remote_async("stock", "stock_payment", (asdict(stock_payment_event),))
    seller_ids = (oi.sellerId for oi in invoice.items)

    seller_notification = PaymentNotification(
        order_id, ctx.key, PaymentStatus.SUCCEEDED
    )

    for seller_id in seller_ids:
        ctx.call_remote_async(
            "seller", "payment_notification", seller_id, (asdict(seller_notification),)
        )

    ctx.call_remote_async(
        "order", "payment_notification", ctx.key, (asdict(seller_notification),)
    )
    ctx.call_remote_async(
        "customer",
        "payment_notification",
        ctx.key,
        (CustomerNotificationType.PAYMENT_SUCCESS,),
    )

    payment_confirmed = PaymentConfirmed(
        customer_checkout,
        order_id,
        invoice.total_invoice,
        invoice.items,
        now,
        customer_checkout.instanceId,
    )

    ctx.call_remote_async(
        "shipment", "payment_confirmed", ctx.key, (payment_confirmed,)
    )  # TODO in tstatefun, they use the number of partitions of the shipment function to get the id. Do we need to?
