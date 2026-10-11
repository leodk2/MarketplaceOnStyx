from dataclasses import asdict
from datetime import datetime

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Packages import Package, PackageStatus
from Entities.Shipment import Shipment, ShipmentStatus
from Requests.CustomerCheckout import PaymentConfirmed, ShipmentNotification
from Requests.DeliveryNotification import DeliveryNotification
from States.ShipmentState import ShipmentState

# keyed by customer_id % n_partitions, so every key is a whole partition
shipment_operator = Operator("shipment")


@shipment_operator.register
async def payment_confirmed(ctx: StatefulFunction, payment_dict: dict):
    payment = PaymentConfirmed(**payment_dict)
    now = datetime.now()
    data = ctx.get()
    shipment_id = data.get("next_id", 1) if data is not None else 1
    shipment = Shipment(
        shipment_id,
        payment.order_id,
        payment.customer_checkout.CustomerId,
        len(payment.items),
        sum(i.freightValue for i in payment.items),
        payment.customer_checkout.FirstName,
        payment.customer_checkout.LastName,
        payment.customer_checkout.Street,
        payment.customer_checkout.ZipCode,
        ShipmentStatus.APPROVED,
        payment.customer_checkout.City,
        payment.customer_checkout.State,
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

    state = ShipmentState(**(data.get("state", {}) if data is not None else {}))
    state.shipment.update({shipment_id: shipment})
    state.packages.update({shipment_id: packages})
    ctx.put(
        {
            "next_id": shipment_id + 1,
            "state": asdict(state),
        }
    )

    notif = ShipmentNotification(
        payment.order_id,
        ShipmentStatus.APPROVED,
        now,
        payment.customer_checkout.CustomerId,
    )

    seller_ids = {oi.sellerId for oi in payment.items}
    for seller_id in seller_ids:
        ctx.call_remote_async(
            "seller", "shipment_notification", seller_id, (asdict(notif),)
        )

    ctx.call_remote_async(
        "order",
        "shipment_notification",
        payment.customer_checkout.CustomerId,
        (asdict(notif),),
    )


@shipment_operator.register
async def update_shipment(ctx: StatefulFunction, tid: str):
    # Invoked by the shipment proxy once per shipment partition. For every
    # seller, deliver the packages of its oldest shipment that is still open.
    data = ctx.get()
    if data is None:
        # nothing has been shipped from this partition yet
        return

    state = ShipmentState(**data.get("state", {}))
    now = datetime.now()

    for seller_id, shipment_id in state.get_oldest_open_shipment_per_seller().items():
        seller_packages = state.get_shipped_packages_by_shipment_id_and_seller_id(
            seller_id, shipment_id
        )
        update_package_delivery(ctx, state, seller_packages, shipment_id, now)

    ctx.put({**data, "state": asdict(state)})


def update_package_delivery(
    ctx: StatefulFunction,
    state: ShipmentState,
    seller_packages: list[Package],
    shipment_id: int,
    now: datetime,
):
    shipment = state.shipment[shipment_id]
    count_delivered = state.get_total_delivered_packages_for_shipment(shipment_id)

    for package in seller_packages:
        package.package_status = PackageStatus.DELIVERED
        package.delivered_time = now

        delivery_notification = DeliveryNotification(
            order_id=package.order_id,
            customer_id=shipment.customer_id,
            package_id=package.package_id,
            seller_id=package.seller_id,
            product_id=package.product_id,
            product_name=package.product_name,
            package_status=PackageStatus.DELIVERED,
            delivery_date=now,
        )

        ctx.call_remote_async(
            "customer", "handle_delivery_notification", shipment.customer_id
        )
        ctx.call_remote_async(
            "seller",
            "handle_delivery_notification",
            package.seller_id,
            (asdict(delivery_notification),),
        )

    if shipment.status == ShipmentStatus.APPROVED:
        shipment.status = ShipmentStatus.DELIVERY_IN_PROGRESS
        notif = ShipmentNotification(
            shipment.order_id, shipment.status, now, shipment.customer_id
        )
        ctx.call_remote_async(
            "order", "shipment_notification", shipment.customer_id, (asdict(notif),)
        )

    if shipment.package_count == count_delivered + len(seller_packages):
        shipment.status = ShipmentStatus.CONCLUDED
        notif = ShipmentNotification(
            shipment.order_id, shipment.status, now, shipment.customer_id
        )

        # Statefun only notifies the seller of this batch of packages
        ctx.call_remote_async(
            "seller",
            "shipment_notification",
            seller_packages[0].seller_id,
            (asdict(notif),),
        )
        ctx.call_remote_async(
            "order", "shipment_notification", shipment.customer_id, (asdict(notif),)
        )

        state.shipment.pop(shipment_id)
        state.packages.pop(shipment_id)


@shipment_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@shipment_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state
