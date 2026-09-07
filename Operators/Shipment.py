from datetime import datetime

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Packages import Package, PackageStatus
from Entities.Shipment import Shipment, ShipmentStatus
from Requests.CustomerCheckout import PaymentConfirmed, ShipmentNotification
from States.ShipmentState import ShipmentState

shipment = Operator("shipment", 4)


@shipment.register
async def payment_confirmed(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentConfirmed(**payment_dict)
    now = datetime.now()
    shipment_id = ctx.get().get("next_id", 0) + 1
    shipment = Shipment(
        shipment_id,
        payment.order_id,
        payment.customer_checkout.customerId,
        len(payment.items),
        sum(i.freightValue for i in payment.items),
        payment.customer_checkout.firstName,
        payment.customer_checkout.lastName,
        payment.customer_checkout.street,
        payment.customer_checkout.zipcode,
        ShipmentStatus.APPROVED,
        payment.customer_checkout.city,
        payment.customer_checkout.state,
        now,
    )

    package_id: int = 1
    packages: list[Package] = []

    for oi in payment.items:
        pkg = Package(
            package_id,
            payment.order_id,
            shipment_id,
            oi.sellerId,
            oi.productId,
            oi.freightValue,
            oi.quantity,
            oi.productName,
            PackageStatus.SHIPPED,
            now,
        )
        packages.append(pkg)
        package_id += 1

    state = ShipmentState(**(ctx.get().get("state", {})))
    state.shipment.update({shipment_id: shipment})
    state.packages.update({shipment_id: packages})
    ctx.put({"next_id": shipment_id, "state": state})

    notif = ShipmentNotification(
        payment.order_id,
        ShipmentStatus.APPROVED,
        now,
        payment.customer_checkout.customerId,
    )

    seller_ids = {oi.sellerId for oi in payment.items}
    for seller_id in seller_ids:
        ctx.call_remote_async("seller", "shipment_notification", seller_id, (notif,))

    ctx.call_remote_async(
        "order", "shipment_notification", payment.customer_checkout.customerId, (notif,)
    )
    # TODO transaction mark/egress message?
