from datetime import datetime

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Packages import Package, PackageStatus
from Entities.Shipment import Shipment, ShipmentStatus
from Requests.CustomerCheckout import PaymentConfirmed, ShipmentNotification
from States.ShipmentState import ShipmentState

shipment = Operator("shipment", 4)

class ShipmentDoesNotExist(Exception):
    pass


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
        "order", 
        "shipment_notification", 
        payment.order_id, 
        (notif,)
    )
    # TODO transaction mark/egress message?


@shipment.register
async def deliver_shipment(ctx: StatefulFunction):
    state = ctx.get()
    if state is None:
        raise ShipmentDoesNotExist("Error: No shipments registered")

    shipment_state = ShipmentState(**(state.get("state", {})))
    oldest_shipments = get_ten_oldest_unconcluded_shipments(shipment_state)

    now = datetime.now()

    for shipment_obj in oldest_shipments:
        shipment_packages = shipment_state.packages.get(shipment_obj.shipment_id, [])
        for package in shipment_packages:
            await deliver_package(ctx, package, now, shipment_obj)
        await deliver_order(ctx, shipment_obj, shipment_packages)

    ctx.put({**state, "state": shipment_state})
    



def get_ten_oldest_unconcluded_shipments(shipment_state: ShipmentState):
    unconcluded_shipments = (
        s for s in shipment_state.shipment.values() if s.status != ShipmentStatus.CONCLUDED
    )
    return sorted(unconcluded_shipments, key=lambda s: s.request_date)[:10]

async def deliver_package(ctx: StatefulFunction, package: Package, now: datetime, shipment_obj: Shipment):
    package.package_status = PackageStatus.DELIVERED
    package.delivered_time = now
    ctx.call_remote_async(
        "seller",
        "handle_delivery_notification",
        package.seller_id,
        (
            {
                "order_id": package.order_id,
                "shipment_id": package.shipment_id,
                "package_id": package.package_id,
                "product_id": package.product_id,
                "status": PackageStatus.DELIVERED.name,
                "event_date": now.isoformat(),
            },
        )
    )
    ctx.call_remote_async(
        "customer",
        "handle_delivery_notification",
        shipment_obj.customer_id
    )
        

async def deliver_order(ctx: StatefulFunction, shipment_obj: Shipment, shipment_packages: list):
    if (all(package.package_status == PackageStatus.DELIVERED for package in shipment_packages)):
        shipment_obj.status = ShipmentStatus.CONCLUDED
        ctx.call_remote_async(
            "order",
            "shipment_notification",
            shipment_obj.order_id,
            (
                ShipmentNotification(
                    shipment_obj.order_id,
                    ShipmentStatus.CONCLUDED,
                    datetime.now(),
                    shipment_obj.customer_id,
                ),
            )
        )
    

