from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.TransactionMark import MarkStatus, TransactionMark, TransactionType
from Operators.Shipment import shipment_operator

# Stateless fan-out to every shipment partition. Unlike statefun, no acks have
# to be counted: all calls run in one styx transaction, so the mark is only
# returned once every partition has been updated.
shipment_proxy_operator = Operator("shipment_proxy")  # keyed by tid


@shipment_proxy_operator.register
async def update_shipment(ctx: StatefulFunction, tid: str):
    for partition in range(shipment_operator.n_partitions):
        ctx.call_remote_async("shipment", "update_shipment", partition, (tid,))

    return TransactionMark(
        tid, TransactionType.UPDATE_DELIVERY, ctx.key, MarkStatus.SUCCESS, "shipment"
    )
