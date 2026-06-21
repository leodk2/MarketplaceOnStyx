from styx.common.stateful_function import StatefulFunction
from logging import Logger
from styx.common.operator import Operator


operator = Operator("order")

logger = Logger(__name__)

@operator.register
async def CheckoutRequest(ctx:StatefulFunction, checkoutRequest: CheckoutRequest):
    pass

@operator.register
async def TryReserve(ctx:StatefulFunction):
    pass

@operator.register
async def PaymentNotification(ctx: StatefulFunction):
    pass

@operator.register
async def ShipmentNotification(ctx:StatefulFunction):
    pass

@operator.register
async def GetOrders(ctx: StatefulFunction):
    # have to check if any state exists
    return ctx.get()
